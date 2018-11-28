import pcbnew
import os
import os.path
import shutil
import sys
import logging
import re
import hashlib
from shutil import copyfile

logger = logging.getLogger(__name__)


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
    with open(filename) as f:
        file_folder = os.path.dirname(os.path.abspath(filename))
        file_lines = f.read()
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


def archive_symbols(board, allow_missing_libraries=False, alt_files=False):
    global __name__
    logger.info("Starting to archive symbols")
    # get project name
    pcb_filename = board.GetFileName()
    project_name = str(os.path.basename(board.GetFileName())).replace(".kicad_pcb", "")
    cache_lib_name = project_name + "-cache.lib"
    archive_lib_name = project_name + "-archive.lib"

    logger.info("Pcb filename:" + pcb_filename)

    # load system symbol library table
    if __name__ != "__main__":
        sys_path = os.path.normpath(pcbnew.GetKicadConfigPath())
    else:
        # hardcode the path for my machine - testing works only on my machine
        sys_path = os.path.normpath("C://Users//MitjaN//AppData//Roaming//kicad//V5")

    logger.info("Kicad config path: " + sys_path)

    global_sym_lib_file_path = os.path.normpath(sys_path + "//sym-lib-table")
    try:
        with open(global_sym_lib_file_path) as f:
            global_sym_lib_file = f.readlines()
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
        with open(proj_sym_lib_file_path) as f:
            project_sym_lib_file = f.readlines()
    # if file does not exists, create new
    except IOError:
        logger.info("Project sym lib table does not exist")
        new_sym_lib_file = [u"(sym_lib_table\n", u")\n"]
        with open(proj_sym_lib_file_path, "w") as f:
            f.writelines(new_sym_lib_file)
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
        with open(proj_sym_lib_file_path, "w") as f:
            f.writelines(project_sym_lib_file)

    # copy cache library
    if not os.path.isfile(os.path.join(proj_path, cache_lib_name)):
        logger.info("Project cache library does not exists!")
        raise IOError("Project cache library does not exists!")
    copyfile(os.path.join(proj_path, cache_lib_name),
             os.path.join(proj_path, archive_lib_name))

    if os.path.isfile(os.path.join(proj_path, cache_lib_name.replace(".lib", ".dcm"))):
        copyfile(os.path.join(proj_path, cache_lib_name.replace(".lib", ".dcm")),
                 os.path.join(proj_path, archive_lib_name.replace(".lib", ".dcm")))

    # read_archive library
    with open(os.path.join(proj_path, archive_lib_name)) as f:
        project_archive_file = f.readlines()

    # first find all symbols in the library
    symbols_list = []
    for line in project_archive_file:
        line_contents = line.split()
        if line_contents[0] == "DEF":
            symbols_list.append(line_contents[1].replace("~", ""))

    # find all symbol referneces and replace them with correct ones
    for symbol in symbols_list:
        # modify the symbol reference
        if symbol.startswith(archive_nick):
            new_symbol = symbol.replace(archive_nick+":", "")
        else:
            new_symbol = symbol.replace(":", "_")
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

    # first add initiali lines
    project_archive_file_output = project_archive_file[0:start_indeces[0]]
    # then only add components which are not duplicated
    tested_components_hash = set()
    for loc in component_locations:
        component = project_archive_file[loc[0]:loc[1]]
        hash_value = hashlib.md5("".join(component)).hexdigest()
        if hash_value not in tested_components_hash:
            tested_components_hash.add(hash_value)
            project_archive_file_output.extend(project_archive_file[loc[0]:loc[1]])
        else:
            print "found one duplicate"
    # add remaining lines
    project_archive_file_output.extend(project_archive_file[stop_indeces[-1]:])

    # writeback the archive file
    with open(os.path.join(proj_path, archive_lib_name), "w") as f:
        f.writelines(project_archive_file_output)

    archive_symbols_list = []
    for sym in symbols_list:
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
        with open(filename) as f:
            sch_file = f.readlines()
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
            line_in_component_decription = False
            for sym_loc in symbol_locations:
                if (sym_loc[0] < index) and (index < sym_loc[1]):
                    line_in_component_decription = True
                    break
            if line_in_component_decription and line_contents[0] == "L":
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
            parts = filename.rsplit(".")
            parts[0] = parts[0]+ "_alt"
            filename = ".".join(parts)

        with open(filename, "w") as f:
            f.writelines(out_files[key])

    # if not testing, delete cache file
    if not alt_files:
        os.remove(os.path.join(proj_path, cache_lib_name))


def archive_3D_models(board, allow_missing_models=False, alt_files=False):
    logger.info("Starting to archive 3D models")
    # load layout
    filename = board.GetFileName()
    logger.info("Pcb filename: " + filename)

    with open(filename) as f:
        pcb_layout = f.readlines()
        f.seek(0, 0)
        pcb_layout_raw = f.read()

    # parse the file
    pcb_layout_nested = balanced_braces(pcb_layout_raw)
    pcb_layout_nested_nested = balanced_braces(pcb_layout_nested)
    # get only modules
    parsed_modules = []
    for entry in pcb_layout_nested_nested:
        if "module" in entry:
            parsed_modules.append(balanced_braces(entry))

    # get models
    parsed_models = []
    for mod in parsed_modules:
        for entry in mod:
            if "model" in entry:
                model = remove_braced_content(entry).replace("model", "").lstrip().rstrip()
                parsed_models.append(model)
    # remove duplicates
    models = list(set(parsed_models))

    path_3d = os.getenv("KISYS3DMOD")
    if path_3d is not None:
        model_library_path = os.path.normpath(path_3d)
    else:
        model_library_path = None

    # if running standalone, enviroment variables might not be set
    if model_library_path is None:
        # hardcode the path for my machine - testing works only on my machine
        model_library_path = os.path.normpath("D://Mitja//Plate//Kicad_libs//official_libs//Packages3D")
    logger.info("KISYS3DMOD path: " + model_library_path)

    # prepare folder for 3dmodels
    proj_path = os.path.dirname(os.path.abspath(board.GetFileName()))
    if alt_files:
        model_folder_path = os.path.normpath(proj_path + "//shapes3D_alt")
    else:
        model_folder_path = os.path.normpath(proj_path + "//shapes3D")
    if not os.path.exists(model_folder_path):
        os.makedirs(model_folder_path)

    # go through the list of used models and replace enviroment variables
    cleaned_models = []
    for model in models:
        # check if path is encoded with variables
        if "${" in model or "$(" in model:
            start_index = model.find("${")+2 or model.find("$(")+2
            end_index = model.find("}") or model.find(")")
            env_var = model[start_index:end_index]
            if env_var != "KISYS3DMOD":
                global __name__
                if __name__ == "__main__":
                    if env_var == "KIPRJMOD":
                        path = os.path.abspath(os.path.dirname(board.GetFileName()))
                else:
                    path = os.getenv(env_var)
            else:
                path = model_library_path
            # if variable is defined, find proper model path
            if path is not None:
                model = os.path.normpath(path+model[end_index+1:])
                cleaned_models.append(model)
            # if variable is not defined, we can not find the model. Thus don't put it on the list
            else:
                logger.info("Can not find model defined with enviroment variable:\n" + model)
        # check if there is no path (model is local to project
        elif model == os.path.basename(model):
            model = os.path.normpath(proj_path + "//" + model)
            cleaned_models.append(model)
        # check if model is given with absolute path
        elif os.path.exists(model):
            cleaned_models.append(model)
        # otherwise we don't know how to parse the path ignorring it
        else:
            logger.info("Can not find model:\n" + model)

    # copy the models
    not_copied = []
    logger.info("Copying 3D models")
    for model in cleaned_models:
        copied_at_least_one = False
        model_without_extension = model.rsplit('.', 1)[0]
        try:
            filepath = model_without_extension + ".wrl"
            shutil.copy2(filepath, model_folder_path)
            copied_at_least_one = True
        # src and dest are the same
        except shutil.Error:
            copied_at_least_one = True
        # file not found
        except (OSError, IOError):
            pass
        try:
            filepath = model_without_extension + ".step"
            shutil.copy2(filepath, model_folder_path)
            copied_at_least_one = True
        # src and dest are the same
        except shutil.Error:
            copied_at_least_one = True
        # file not found
        except (OSError, IOError):
            pass
        try:
            filepath = model_without_extension + ".stp"
            shutil.copy2(filepath, model_folder_path)
            copied_at_least_one = True
        # src and dest are the same
        except shutil.Error:
            copied_at_least_one = True
        # file not found
        except (OSError, IOError):
            pass
        try:
            filepath = model_without_extension + ".igs"
            shutil.copy2(filepath, model_folder_path)
            copied_at_least_one = True
        # src and dest are the same
        except shutil.Error:
            copied_at_least_one = True
        # file not found
        except (OSError, IOError):
            pass
        if not copied_at_least_one:
            not_copied.append(model)

    if not_copied:
        if not allow_missing_models:
            not_copied_pretty = []
            for x in not_copied:
                not_copied_pretty.append(os.path.normpath(x))
            logger.info("Did not suceed to copy 3D models!")
            raise IOError("Did not suceed to copy 3D models!\n"
                          "Did not find:\n" + "\n".join(not_copied_pretty))

    # generate output file with project relative path
    out_file = []
    for line in pcb_layout:
        line_new = line
        for mod in models:
            if mod in line:
                model_name = os.path.basename(os.path.normpath(mod)).strip('"')
                if alt_files:
                    new_model_path = "${KIPRJMOD}/" + "shapes3D_alt/" + model_name
                else:
                    new_model_path = "${KIPRJMOD}/" + "shapes3D/" + model_name
                # if enclosed with doublequotes, enclose line_new also
                if "\"" in mod:
                    new_model_path = "\"" + new_model_path + "\""
                line_new = line.replace(mod, new_model_path)
                pass
        out_file.append(line_new)
    # write
    if alt_files:
        parts = filename.rsplit(".")
        parts[0] = parts[0] + "_alt"
        filename = ".".join(parts)
    with open(filename, "w") as f:
        logger.info("Writing to pcb layout file:"+filename)
        f.writelines(out_file)
    pass


def main():
    #board = pcbnew.LoadBoard('fresh_test_project/archive_test_project.kicad_pcb')
    board = pcbnew.LoadBoard('archived_test_project/archive_test_project.kicad_pcb')
    try:
        archive_symbols(board, allow_missing_libraries=True, alt_files=True)
    except (ValueError, IOError, LookupError), error:
        print str(error)
    except NameError as error:
        print str(error)
    try:
        archive_3D_models(board, allow_missing_models=False, alt_files=True)
    except IOError as error:
        archive_3D_models(board, allow_missing_models=True, alt_files=True)
        print str(error)


# for testing purposes only
if __name__ == "__main__":
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
    logger.info("Archive plugin started in standalone mode")

    main()




