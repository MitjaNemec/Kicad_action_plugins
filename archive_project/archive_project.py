from __future__ import absolute_import, division, print_function
import pcbnew
import os
import os.path
import shutil
import sys
import logging
import re
import hashlib
from shutil import copyfile
try:
    from urllib import urlretrieve
except:
    from urllib.request import urlretrieve


logger = logging.getLogger(__name__)

# get version information
version_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
with open(version_filename, 'rb') as f:
    # read and decode
    version_file_contents = f.read().decode('utf-8')
    # extract first line
    VERSION = version_file_contents.split('\n')[0].strip()

# > V5.1.5 and V 5.99 build information
if hasattr(pcbnew, 'GetBuildVersion'):
    BUILD_VERSION = pcbnew.GetBuildVersion()
else:
    BUILD_VERSION = "Unknown"
    

def balanced_braces(args):
    if isinstance(args, str):
        args = [args]
    parts = []
    for arg in args:
        if '(' not in arg:
            continue
        chars = []
        n = 0
        for c in arg:
            if c == '(':
                if n > 0:
                    chars.append(c)
                n += 1
            elif c == ')':
                n -= 1
                if n > 0:
                    chars.append(c)
                elif n == 0:
                    parts.append(''.join(chars).lstrip().rstrip())
                    chars = []
            elif n > 0:
                chars.append(c)
    return parts


def remove_braced_content(args):
    if isinstance(args, str):
        args = [args]
    parts = []
    for arg in args:
        if '(' not in arg:
            continue
        chars = []
        n = 0
        for c in arg:
            if c == '(':
                n += 1
            elif c == ')':
                n -= 1
                if n == 0:
                    parts.append(''.join(chars).lstrip().rstrip())
                    chars = []
            elif n == 0:
                chars.append(c)
    return " ".join(parts)


def extract_subsheets(filename):
    with open(filename, 'rb') as f:
        file_folder = os.path.dirname(os.path.abspath(filename))
        file_lines = f.read().decode('utf-8')
    # alternative solution
    # extract all sheet references
    sheet_indices = [m.start() for m in re.finditer('\$Sheet', file_lines)]
    endsheet_indices = [m.start() for m in re.finditer('\$EndSheet', file_lines)]

    if len(sheet_indices) != len(endsheet_indices):
        raise LookupError("Schematic page contains errors")

    sheet_locations = zip(sheet_indices, endsheet_indices)
    for sheet_location in sheet_locations:
        sheet_reference = file_lines[sheet_location[0]:sheet_location[1]].split('\n')
        for line in sheet_reference:
            if line.startswith('F1 '):
                subsheet_path = line.split("\"")[1]
                subsheet_line = file_lines.split("\n").index(line)

                if not os.path.isabs(subsheet_path):
                    # check if path is encoded with variables
                    if "${" in subsheet_path:
                        start_index = subsheet_path.find("${") + 2
                        end_index = subsheet_path.find("}")
                        env_var = subsheet_path[start_index:end_index]
                        path = os.getenv(env_var)
                        # if variable is not defined rasie an exception
                        if path is None:
                            raise LookupError("Can not find subsheet: " + subsheet_path)
                        # replace variable with full path
                        subsheet_path = subsheet_path.replace("${", "") \
                            .replace("}", "") \
                            .replace("env_var", path)

                # if path is still not absolute, then it is relative to project
                if not os.path.isabs(subsheet_path):
                    subsheet_path = os.path.join(file_folder, subsheet_path)

                subsheet_path = os.path.normpath(subsheet_path)
                # found subsheet reference go for the next one, no need to parse further
                break
        yield subsheet_path, subsheet_line


def find_all_sch_files(filename, list_of_files):
    list_of_files.append(filename)

    for sheet, line_nr in extract_subsheets(filename):
        logger.info("found subsheet:\n\t" + sheet +
                    "\n\t in:\n\t" + filename + ", line: " + str(line_nr))
        seznam = find_all_sch_files(sheet, list_of_files)
        list_of_files = seznam
    return list_of_files


def archive_worksheet(board):
    logger.info("Starting to archive worksheets")
    # get project name
    pcb_filename = os.path.abspath(board.GetFileName())
    project_name = pcb_filename.replace(".kicad_pcb", ".pro")
    project_dir = os.path.dirname(project_name)
    # open project file
    with open(project_name, 'rb') as f:
        file_contents = f.read().decode('utf-8')
        project_file = file_contents.split('\n')

    # find worksheet entry
    for line_index in range(len(project_file)):
        line = project_file[line_index]
        if line.startswith("PageLayoutDescrFile="):
            file_descriptor = line.lstrip("PageLayoutDescrFile=").rstrip()
            logger.info("Found worksheet entry: " + file_descriptor + " at line: " + str(line_index))
            worksheet_path = os.path.abspath(file_descriptor)
            logger.info("Full worksheet path: " + worksheet_path)

            if not os.path.isfile(worksheet_path):
                logger.info("Worksheet file does not exist")
                # I don't dare to change the project file in this case
                continue
            logger.info("Worksheet file does exist")

            # try to open the file to see if we've got read access
            try:
                with open(worksheet_path, 'rb') as f:
                    logger.info("Worksheet file exists and we can read it")
            except IOError:
                logger.info("Worksheet file exists but is not accessible")
                raise IOError

            worksheet_filename = os.path.basename(worksheet_path)
            line_index = project_file.index(line)

            # copy worksheet to local path
            destination_path = os.path.join(project_dir, worksheet_filename)
            try:
                shutil.copy2(worksheet_path, os.path.join(project_dir, destination_path))
            except shutil.Error:
                logger.info("Destination file: " + destination_path + " already exists.")
            except OSError as e:
                logger.info("Source file: " + worksheet_path + " does not exist.")
                raise e
            except IOError as e:
                logger.info("Can not access the source file: " + worksheet_path)
                raise e

            # try writing the project file
            new_line = "PageLayoutDescrFile=" + worksheet_filename + "\n"
            project_file[line_index] = new_line

    with open(project_name, "wb") as f:
        project_file_contents = ''.join(project_file)
        f.write(project_file_contents.encode('utf-8'))


def archive_symbols(board, allow_missing_libraries=False, alt_files=False, archive_documentation=False):
    global __name__
    logger.info("Starting to archive symbols")
    # get project name
    pcb_filename = board.GetFileName()
    project_name = str(os.path.basename(board.GetFileName())).replace(".kicad_pcb", "")
    cache_lib_name = project_name + "-cache.lib"
    archive_lib_name = project_name + "-archive.lib"

    logger.info("Pcb filename:" + pcb_filename)

    # list of failed documentation file accesses
    documentation_failed = []

    # load system symbol library table
    if __name__ != "__main__":
        sys_path = os.path.normpath(pcbnew.GetKicadConfigPath())
    else:
        # hardcode the path for my machine - testing works only on my machine
        sys_path = os.path.normpath("C://Users//MitjaN//AppData//Roaming//kicad")

    logger.info("Kicad config path: " + sys_path)

    global_sym_lib_file_path = os.path.normpath(sys_path + "//sym-lib-table")
    try:
        with open(global_sym_lib_file_path, 'rb') as f:
            file_contents = f.read().decode('utf-8')
            global_sym_lib_file = file_contents.split('\n')
    except IOError:
        logger.info("Global sym-lib-table does not exist!")
        raise IOError("Global sym-lib-table does not exist!")

    # get library nicknames and dictionary of libraries (nickame:uri)
    libraries = {}
    nicknames = []
    for line in global_sym_lib_file:
        nick_start = line.find("(name ")+6
        if nick_start >= 6:
            nick_stop = line.find(")", nick_start)
            nick = line[nick_start:nick_stop]
            nicknames.append(nick)
            # find path to library
            path_start = line.find("(uri ")+5
            if path_start >= 5:
                path_stop = line.find(")", path_start)
                path = line[path_start:path_stop]
                libraries[path] = nick

    # load project library table
    proj_path = os.path.dirname(os.path.abspath(board.GetFileName()))
    proj_sym_lib_file_path = os.path.normpath(proj_path + "//sym-lib-table")
    try:
        with open(proj_sym_lib_file_path, 'rb') as f:
            file_contents = f.read().decode('utf-8')
            project_sym_lib_file = file_contents.split('\n')
    # if file does not exists, create new
    except IOError:
        logger.info("Project sym lib table does not exist")
        new_sym_lib_file = [u"(sym_lib_table\n", u")\n"]
        with open(proj_sym_lib_file_path, 'wb') as f:
            f.write("".join(new_sym_lib_file).encode('utf-8'))
            project_sym_lib_file = new_sym_lib_file
    # append nicknames
    for line in project_sym_lib_file:
        nick_start = line.find("(name ")+6
        if nick_start >= 6:
            nick_stop = line.find(")", nick_start)
            nick = line[nick_start:nick_stop]
            nicknames.append(nick)

            path_start = line.find("(uri ")+5
            if path_start >= 5:
                path_stop = line.find(")", path_start)
                path = line[path_start:path_stop]
                libraries[path] = nick

    # check if archive library is already linked in
    archive_nick = None
    for lib in libraries.keys():
        # if archive is already linked in, use its nickname
        if archive_lib_name in lib:
            logger.info("project-archive.lib is already in the sym-lib-table, using its nickname")
            archive_nick = libraries[lib]
            break
        # if archive is not linked
        else:
            # check if default nick is already taken
            if libraries[lib] == "archive":
                logger.info("Nickname \"archive\" already taken")
                raise ValueError("Nickname \"archive\" already taken by library that is not a project cache library!")

    if archive_nick is None:
        archive_nick = "archive"
        logger.info("Entering archive library in sym-lib-table")
        line_contents = "    (lib (name archive)(type Legacy)(uri \"${KIPRJMOD}/" + archive_lib_name + "\")(options \"\")(descr \"\"))\n"
        project_sym_lib_file.insert(1, line_contents)
        with open(proj_sym_lib_file_path, 'wb') as f:
            f.write("".join(project_sym_lib_file).encode('utf-8'))

    # copy cache library and overwrite acrhive library, if it exists
    if not os.path.isfile(os.path.join(proj_path, cache_lib_name)):
        logger.info("Project cache library does not exists!")
        raise IOError("Project cache library does not exists!")
    copyfile(os.path.join(proj_path, cache_lib_name),
             os.path.join(proj_path, archive_lib_name))

    if os.path.isfile(os.path.join(proj_path, cache_lib_name.replace(".lib", ".dcm"))):
        copyfile(os.path.join(proj_path, cache_lib_name.replace(".lib", ".dcm")),
                 os.path.join(proj_path, archive_lib_name.replace(".lib", ".dcm")))

    # read_archive library
    with open(os.path.join(proj_path, archive_lib_name), 'rb') as f:
        file_contents = f.read().decode('utf-8')
        project_archive_file = file_contents.split('\n')

    # first find all symbols in the library
    symbols_list = []
    for line in project_archive_file:
        line_contents = line.split()
        if line_contents and line_contents[0] == "DEF":
            symbols_list.append(line_contents[1].replace("~", ""))

    # find all symbol references and replace them with correct ones
    new_symbol_list = []
    for symbol in symbols_list:
        # modify the symbol reference
        if symbol.startswith(archive_nick):
            new_symbol = symbol.replace(archive_nick+":", "")
            new_symbol = symbol.replace(archive_nick+"_", "")
        else:
            new_symbol = symbol.replace(":", "_")
        new_symbol_list.append(new_symbol)
        for line in project_archive_file:
            index = project_archive_file.index(line)
            if symbol in line and not line.startswith("F2"):
                project_archive_file[index] = line.replace(symbol, new_symbol)

    # scan for duplicate symbols and remove them
    # TODO
    start_indeces = []
    stop_indeces = []
    for index, line in enumerate(project_archive_file):
        if line.startswith("DEF"):
            start_indeces.append(index-3)
        if line.startswith("ENDDEF"):
            stop_indeces.append(index+1)
    component_locations = zip(start_indeces, stop_indeces)

    # first add initial lines
    project_archive_file_output = project_archive_file[0:start_indeces[0]]
    # then only add components which are not duplicated
    tested_components_hash = set()
    for loc in component_locations:
        component = project_archive_file[loc[0]:loc[1]]
        hash_value = hashlib.md5("".join(component).encode('utf-8')).hexdigest()
        if hash_value not in tested_components_hash:
            tested_components_hash.add(hash_value)
            project_archive_file_output.extend(project_archive_file[loc[0]:loc[1]])
        else:
            print("found one duplicate")
    # add remaining lines
    project_archive_file_output.extend(project_archive_file[stop_indeces[-1]:])

    # writeback the archive file
    with open(os.path.join(proj_path, archive_lib_name), 'wb') as f:
        f.write("\n".join(project_archive_file_output).encode('utf-8'))

    archive_symbols_list = []
    for sym in new_symbol_list:
        if sym.startswith(archive_nick):
            archive_symbols_list.append(sym.split(':', 1)[-1])
        else:
            archive_symbols_list.append(sym.replace(":","_"))
    archive_symbols_list = list(set(archive_symbols_list))

    # find all .sch files
    # open main schematics file and look fo any sbuhiearchical files. In any subhierachical file scan for any sub-sub
    main_sch_file = os.path.abspath(str(pcb_filename).replace(".kicad_pcb", ".sch"))

    all_sch_files = []
    all_sch_files = find_all_sch_files(main_sch_file, all_sch_files)
    all_sch_files = list(set(all_sch_files))

    logger.info("found all subsheets")
    # go through each .sch file
    out_files = {}
    symbols_form_missing_libraries = set()
    for filename in all_sch_files:
        out_files[filename] = []
        with open(filename, 'rb') as f:
            file_contents = f.read().decode('utf-8')
            sch_file = file_contents.split('\n')
            logger.info("Archiving file: " + filename)

        # go throught the symbols only
        def_indices = []
        enddef_indices = []
        for index, line in enumerate(sch_file):
            if line.startswith('$Comp'):
                def_indices.append(index)
            if line.startswith('$EndComp'):
                enddef_indices.append(index)
        if len(def_indices) != len(enddef_indices):
            logger.info("Cache library contains errors")
            raise LookupError("Cache library contains errors")
        symbol_locations = zip(def_indices, enddef_indices)

        sch_file_out = []
        # find line starting with L and next word until colon mathes library nickname
        for index, line in enumerate(sch_file):

            line_contents = line.split()
            # if line is within the componend description and line denotes a symbol label
            for sym_loc in symbol_locations:
                if (sym_loc[0] < index) and (index < sym_loc[1]):
                    break
            # if line begins with L it is the library reference                    
            if line_contents[0] == "L":
                libraryname = line_contents[1].split(":")[0]
                symbolname = line_contents[1].split(":")[1]
                # replace colon with underscore
                if libraryname == archive_nick:
                    new_name = symbolname.split(archive_nick+'_', 1)[-1]
                else:
                    new_name = line_contents[1].replace(":", "_")

                # make sure that the symbol is in cache and append cache nickname
                if new_name in archive_symbols_list:
                    line_contents[1] = archive_nick + ":" + new_name
                # if the symbol is not in cache raise exception
                else:
                    logger.info("Trying to remap symbol which does not exist in archive library. Archive library is incomplete")
                    raise LookupError(
                        "Symbol \"" + new_name + "\" is not present in archive libray. Archive library is incomplete")
                # join line back again
                new_line = ' '.join(line_contents)
                sch_file_out.append(new_line + "\n")

                # symbol is not from the library present on the system markit for the potential errormessage
                if libraryname not in nicknames:
                    symbols_form_missing_libraries.add(symbolname)
            # if it begins with F3 it might be a data sheet entry
            elif line_contents[0] == "F" and line_contents[1] == "3" and archive_documentation is True:
                link = line_contents[2].lower()
                if len(link) > 10:
                    logger.info("Trying to archive documentation file: " + link)
                    # if it is an url
                    if (link.startswith("http") or link.startswith("\"http")
                        or link.startswith("https") or link.startswith("\"https")
                        or link.startswith("www") or link.startswith("\"www"))\
                        and (link.endswith(".pdf") or link.endswith(".pdf\"")):

                        logger.info("File is encoded with URL")
                        if link.startswith("\""):
                            link = link.strip("\"")
                        if link.startswith("www"):
                            link = "https://" + link

                        # try to get the file
                        doc_filename = os.path.basename(link)
                        destination_dir = os.path.join(proj_path, "documentation")
                        destination_path = os.path.join(destination_dir, doc_filename)
                        # check if folder exists
                        if not os.path.exists(destination_dir):
                            os.mkdir(destination_dir)

                        try:
                            # download file
                            logger.info("Downloading file")
                            urlretrieve(link, destination_path)
                            # remap the entry
                            logger.info("Remapping documenation entry")
                            line_contents[2] = "\"" + "${KIPRJMOD}/documentation/" + doc_filename + "\""
                            new_line = ' '.join(line_contents)
                            sch_file_out.append(new_line + "\n")
                        except:
                            logger.info("Failed to download file")
                            documentation_failed.append(link)
                            sch_file_out.append(line)
                            pass

                    # otherwise it is a filepath
                    else:
                        logger.info("File is encoded with filepath")
                        clean_model_path = os.path.normpath(link.strip("\""))
                        # check if it can be expanded via accessible environment variables
                        if "${" in clean_model_path or "$(" in clean_model_path:
                            start_index = clean_model_path.find("${")+2 or clean_model_path.find("$(")+2
                            end_index = clean_model_path.find("}") or clean_model_path.find(")")
                            env_var = clean_model_path[start_index:end_index]
                            if env_var == "KIPRJMOD":
                                path = proj_path
                            else:
                                path = os.getenv(env_var)
                            # if variable is defined, find proper model path
                            if path is not None:
                                logger.info("File had enviroment variable")
                                clean_model_path = os.path.normpath(path+clean_model_path[end_index+1:])
                            # if variable is not defined, we can not find the model. Thus don't put it on the list
                            else:
                                logger.info("Can not find documentation defined with enviroment variable:\n" + link)

                        try:
                            # copy the file localy
                            logger.info("Trying to copy the file")
                            doc_filename = os.path.basename(clean_model_path)
                            destination_dir = os.path.join(proj_path, "documentation")
                            destination_path = os.path.join(destination_dir, doc_filename)
                            shutil.copy2(clean_model_path, destination_path)
                            # and remap the entry
                            logger.info("Remapping documenation entry")
                            line_contents[2] = "\"" + "${KIPRJMOD}/documentation/" + doc_filename + "\""
                            new_line = ' '.join(line_contents)
                            sch_file_out.append(new_line + "\n")
                        # src and dest are the same
                        except shutil.Error:
                            logger.info("File has already been archived")
                            documentation_failed.append(link)
                            sch_file_out.append(line)
                        # file not found
                        except (OSError, IOError) as e:
                            logger.info("Failed to copy file")
                            documentation_failed.append(link)
                            sch_file_out.append(line)
                else:
                    sch_file_out.append(line)
            # othrerwise, just copy the line
            else:
                sch_file_out.append(line)
        # prepare for writing
        out_files[filename] = sch_file_out

    if symbols_form_missing_libraries:
        if not allow_missing_libraries:
            logger.info("Schematics includes symbols from the libraries not present on the system\n"
                        "Did Not Find:\n" + "\n".join(symbols_form_missing_libraries))
            raise NameError("Schematics includes symbols from the libraries not present on the system\n"
                            "Did Not Find:\n" + "\n".join(symbols_form_missing_libraries))

    # if no exceptions has been raised write files
    logger.info("Writing schematics file(s)")
    for key in out_files:
        filename = key
        # write
        if alt_files:
            filename = filename.replace(".sch", "_temp.sch")
        with open(filename, 'wb') as f:
            f.write("".join(out_files[key]).encode('utf-8'))

    # if not testing, delete cache file
    if not alt_files:
        os.remove(os.path.join(proj_path, cache_lib_name))


def archive_3D_models(board, allow_missing_models=False, alt_files=False):
    logger.info("Starting to archive 3D models")

    logger.info("All defined environment variables: " + repr(os.environ))

    # if running standalone, environment variables might not be set
    if os.getenv("KISYS3DMOD") is None:
        # hardcode the path for my machine - testing works only on my machine
        os.environ["KISYS3DMOD"] = os.path.normpath("D://Mitja//Plate//Kicad_libs//official_libs//Packages3D")
    if os.getenv("KIPRJMOD") is None:
        # hardcode the path for my machine - testing works only on my machine
        os.environ["KIPRJMOD"] = os.path.abspath(os.path.dirname(board.GetFileName()))

    # prepare folder for 3Dmodels
    proj_path = os.path.dirname(os.path.abspath(board.GetFileName()))
    if alt_files:
        model_folder_path = os.path.normpath(proj_path + "//shapes3D_temp")
    else:
        model_folder_path = os.path.normpath(proj_path + "//shapes3D")
    if not os.path.exists(model_folder_path):
        os.makedirs(model_folder_path)

    # get all modules
    modules = board.GetModules()

    # go through all modules
    not_copied = []
    for mod in modules:
        logger.debug("Getting 3D models for footprint of: " + mod.GetReference())
        # find all 3D models linked to module(footprint)
        models = mod.Models()
        # go thorugh all models bound to module
        # bad python API
        nr_models = range(len(models))
        for index in nr_models:
            # pop one module from the list
            model = models.pop()
            # copy 3D model
            model_path = model.m_Filename
            logger.debug("Trying to copy: " + model_path)

            # check if path is encoded with variables
            if "${" in model_path or "$(" in model_path:
                start_index = model_path.find("${")+2 or model_path.find("$(")+2
                end_index = model_path.find("}") or model_path.find(")")
                env_var = model_path[start_index:end_index]

                path = os.getenv(env_var)

                # if variable is defined, find proper model path
                if path is not None:
                    clean_model_path = os.path.normpath(path+model_path[end_index+1:])
                # if variable is not defined, we can not find the model. Thus don't put it on the list
                else:
                    logger.info("Can not find model defined with enviroment variable:\n" + model_path)
            # check if there is no path (model is local to project
            elif model_path == os.path.basename(model_path):
                clean_model_path = os.path.normpath(proj_path + "//" + model_path)
            # check if model is given with absolute path
            elif os.path.exists(model_path):
                clean_model_path = model_path
            # otherwise we don't know how to parse the path
            else:
                logger.info("Ambiguios path for the model: " + model_path)
                # test default 3D_library location "KISYS3DMOD"
                if os.path.exists(os.path.normpath(os.path.join(os.getenv("KISYS3DMOD"),model_path))):
                    # testin project folder location
                    clean_model_path = os.path.normpath(os.path.join(os.getenv("KISYS3DMOD"),model_path))
                    logger.info("Going with: " + clean_model_path)
                elif os.path.exists(os.path.normpath(os.path.join(proj_path,model_path))):
                    clean_model_path = os.path.normpath(os.path.join(proj_path,model_path))
                    logger.info("Going with: " + clean_model_path)
                else:
                    logger.info("Can not find model defined with enviroment variable:\n" + model_path)
                    clean_model_path = None

            # copy model
            copied_at_least_one = False
            if clean_model_path:
                model_without_extension = clean_model_path.rsplit('.', 1)[0]
                for ext in ['.wrl', '.stp', '.step', '.igs']:
                    try:
                        shutil.copy2(model_without_extension + ext, model_folder_path)
                        copied_at_least_one = True
                    # src and dest are the same
                    except shutil.Error:
                        copied_at_least_one = True
                    # file not found
                    except (OSError, IOError):
                        pass

            if not copied_at_least_one:
                logger.debug("Did not copy: " + model.m_Filename + " at: " + clean_model_path)
                not_copied.append(model.m_Filename)

            if copied_at_least_one or allow_missing_models:
                logger.debug("Remapping: " + model.m_Filename)
                filename = os.path.basename(clean_model_path)
                new_path = "${KIPRJMOD}/shapes3D/" + filename
                model.m_Filename = new_path

            # and push it to the back of the list (changed or unchaged)
            models.push_back(model)

    if not_copied:
        if not allow_missing_models:
            not_copied_pretty = [os.path.normpath(x) for x in not_copied]
            logger.info("Did not succeed to copy 3D models!")
            raise IOError("Did not succeed to copy 3D models!\n"
                          "Did not find:\n" + "\n".join(not_copied_pretty))


def main():
    #board = pcbnew.LoadBoard('fresh_test_project/archive_test_project.kicad_pcb')
    board = pcbnew.LoadBoard('archived_test_project/archive_test_project.kicad_pcb')
    try:
        archive_symbols(board, allow_missing_libraries=True, alt_files=True, archive_documentation=True)
    except (ValueError, IOError, LookupError) as error:
        print(str(error))
    except NameError as error:
        print(str(error))

    archive_worksheet(board)

    try:
        archive_3D_models(board, allow_missing_models=False, alt_files=True)
    except IOError as error:
        archive_3D_models(board, allow_missing_models=True, alt_files=True)
        print(str(error))
    saved = pcbnew.SaveBoard(board.GetFileName().replace(".kicad_pcb", "_temp.kicad_pcb"), board)


# for testing purposes only
if __name__ == "__main__":
    # if debugging outside of this folder change the folder
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    file_handler = logging.FileHandler(filename='archive_project.log', mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]
    # handlers = [file_handler]

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        handlers=handlers
                        )

    logger = logging.getLogger(__name__)
    logger.info("Plugin executed on: " + repr(sys.platform))
    logger.info("Plugin executed with python version: " + repr(sys.version))
    logger.info("KiCad build version: " + BUILD_VERSION)
    logger.info("Archive plugin version: " + VERSION + " started in standalone mode")

    main()
