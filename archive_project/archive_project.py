import pcbnew
import os
import os.path
import shutil
import wx
import sys
import logging
from collections import defaultdict

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


def is_pcbnew_running():
    windows = wx.GetTopLevelWindows()
    if len(windows) == 0:
        return False
    else:
        return True


def extract_subsheets(filename):
    in_rec_mode = False
    counter = 0
    with open(filename) as f:
        file_folder = os.path.dirname(os.path.abspath(filename))
        file_lines = f.readlines()
    for line in file_lines:
        counter += 1
        if not in_rec_mode:
            if line.startswith('$Sheet'):
                in_rec_mode = True
                subsheet_path = []
        elif line.startswith('$EndSheet'):
            in_rec_mode = False
            yield subsheet_path
        else:
            #extract subsheet path
            if line.startswith('F1'):
                subsheet_path = line.split()[1].rstrip("\"").lstrip("\"")
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
                        subsheet_path = subsheet_path.replace("${", "")\
                                                     .replace("}", "")\
                                                     .replace("env_var", path)

                # if path is still not absolute, then it is relative to project
                if not os.path.isabs(subsheet_path):
                    subsheet_path = os.path.join(file_folder, subsheet_path)

                subsheet_path = os.path.normpath(subsheet_path)
                pass


def find_all_sch_files(filename, list_of_files):
    list_of_files.append(filename)
    for sheet in extract_subsheets(filename):
        seznam = find_all_sch_files(sheet, list_of_files)
        list_of_files = seznam
    return list_of_files


def archive_symbols(board, allow_missing_libraries=False, alt_files=False):
    logger.info("Starting to archive symbols")
    # get project name
    pcb_filename = board.GetFileName()
    project_name = str(os.path.basename(board.GetFileName())).replace(".kicad_pcb", "")
    cache_lib_name = project_name + "-cache.lib"

    logger.info("Pcb filename:" + pcb_filename)

    # load system symbol library table
    if is_pcbnew_running():
        sys_path = pcbnew.GetKicadConfigPath()
    else:
        # hardcode the path for my machine - testing works only on my machine
        sys_path = os.path.normpath("C://Users//MitjaN//AppData//Roaming//kicad")

    logger.info("Kicad config path: " + sys_path)

    global_sym_lib_file_path = os.path.normpath(sys_path + "//sym-lib-table")
    with open(global_sym_lib_file_path) as f:
        global_sym_lib_file = f.readlines()

    # get add library nicknames
    nicknames = []
    for line in global_sym_lib_file:
        nick_start = line.find("(name ")+6
        if nick_start >= 6:
            nick_stop = line.find(")", nick_start)
            nick = line[nick_start:nick_stop]
            nicknames.append(nick)

    # load project library table
    proj_path = os.path.dirname(os.path.abspath(board.GetFileName()))
    proj_sym_lib_file_path = os.path.normpath(proj_path + "//sym-lib-table")
    try:
        with open(proj_sym_lib_file_path) as f:
            project_sym_lib_file = f.readlines()
    # if file does not exists, create new
    except:
        logger.info("Project sym lib table does not exist")
        new_sym_lib_file = [u"(sym_lib_table\n", u")\n"]
        with open(proj_sym_lib_file_path, "w") as f:
            f.writelines(new_sym_lib_file)
            project_sym_lib_file = new_sym_lib_file
    # append nicknames
    cache_nick = "cache"
    for line in project_sym_lib_file:
        nick_start = line.find("(name ")+6
        if nick_start >= 6:
            nick_stop = line.find(")", nick_start)
            nick = line[nick_start:nick_stop]
            nicknames.append(nick)

            # check if library is project cache library
            name_start = line.find("(uri ") + 5
            name_end = line.find(")(options ")
            if cache_lib_name in line[name_start:name_end]:
                cache_nick = nick
                logger.info("project-cache.lib is already in the sym-lib-table, using its nickname")

    # if there is already nickname cache but no actual cache-lib
    if cache_nick in nicknames and cache_lib_name not in unicode(project_sym_lib_file):
        # throw an exception
        logger.info("Nickname \"cache\" already taken")
        raise ValueError("Nickname \"cache\" already taken by library that is not a project cache library!")

    # if cache library is not on the list, put it there
    if cache_lib_name not in unicode(project_sym_lib_file):
        logger.info("Entering cache library in sym-lib-table")
        line_contents = "    (lib (name cache)(type Legacy)(uri ${KIPRJMOD}/" + cache_lib_name + ")(options \"\")(descr \"\"))\n"
        project_sym_lib_file.insert(1, line_contents)
        with open(proj_sym_lib_file_path, "w") as f:
            f.writelines(project_sym_lib_file)

    # load cache library
    proj_cache_ling_path = os.path.join(proj_path, cache_lib_name)
    try:
        with open(proj_cache_ling_path) as f:
            project_cache_file = f.readlines()
    # if file does not exists, raise exception
    except:
        logger.info("Project cache library does not exists!")
        raise IOError("Project cache library does not exists!")

    # get list of symbols in cache library
    cache_symbols = []
    for line in project_cache_file:
        line_contents = line.split()
        if line_contents[0] == "DEF":
            # remove any "~"
            cache_symbol = line_contents[1].replace("~", "")
            cache_symbols.append(cache_symbol)

    # find all .sch files
    # open main schematics file and look fo any sbuhiearchical files. In any subhierachical file scan for any sub-sub
    main_sch_file = os.path.abspath(str(pcb_filename).replace(".kicad_pcb", ".sch"))

    all_sch_files = []
    all_sch_files = find_all_sch_files(main_sch_file, all_sch_files)
    all_sch_files = list(set(all_sch_files))

    # go through each .sch file
    out_files = {}
    symbols_form_missing_libraries = set()
    for filename in all_sch_files:
        out_files[filename] = []
        with open(filename) as f:
            sch_file = f.readlines()

        sch_file_out = []
        # find line starting with L and next word until colon mathes library nickname
        for line in sch_file:
            line_contents = line.split()
            # find symbol name
            if line_contents[0] == "L":
                libraryname = line_contents[1].split(":")[0]
                symbolname = line_contents[1].split(":")[1]
                # replace colon with underscore
                new_name = line_contents[1].replace(":", "_")
                # make sure that the symbol is in cache and append cache nickname
                if new_name in cache_symbols:
                    line_contents[1] = cache_nick + ":" + new_name
                # if the symbol is not in cache raise exception
                else:
                    logger.info("Trying to remap symbol which does not exist in cache library. Cache library is incomplete")
                    raise LookupError(
                        "Symbol \"" + new_name + "\" is not present in cache libray. Cache library is incomplete")
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
            logger.info("Schematics includes symbols from the libraries not present on the system")
            raise NameError("Schematics includes symbols from the libraries not present on the system\n"
                            "Did Not Find:\n" + "\n".join(symbols_form_missing_libraries))

    # if no exceptions has been raised write files
    logger.info("Writing schematics file")
    for key in out_files:
        filename = key
        # write
        if alt_files:
            filename = key + "_alt"

        with open(filename, "w") as f:
            f.writelines(out_files[key])
            pass
    pass


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

    model_library_path = os.getenv("KISYS3DMOD")
    # if running standalone, enviroment variables might not be set
    if model_library_path is None:
        # hardcode the path for my machine - testing works only on my machine
        model_library_path = os.path.normpath("D://Mitja//Plate//Kicad_libs//official_libs//Packages3D")
    logger.info("KISYS3DMOD path: " + model_library_path)

    # prepare folder for 3dmodels
    proj_path = os.path.dirname(os.path.abspath(board.GetFileName()))
    model_folder_path = os.path.normpath(proj_path + "//shapes3D")
    if not os.path.exists(model_folder_path):
        os.makedirs(model_folder_path)

    # go through the list of used models and replace enviroment variables
    cleaned_models = []
    for model in models:
        # check if path is encoded with variables
        if "${" in model:
            start_index = model.find("${")+2
            end_index = model.find("}")
            env_var = model[start_index:end_index]
            if env_var != "KISYS3DMOD":
                path = os.getenv(env_var)
            else:
                path = model_library_path
            # if variable is defined, find proper model path
            if path is not None:
                model = os.path.normpath(path+model[end_index+1:])
                cleaned_models.append(model)
            # if variable is not defined, we can not find the model. Thus don't put it on the list
            else:
                pass
        # check if there is no path (model is local to project
        elif model == os.path.basename(model):
            model = os.path.normpath(proj_path + "//" + model)
            cleaned_models.append(model)
        # if model is referenced with absolute path, we don't need to do anything
        else:
            cleaned_models.append(model)

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
        except:
            pass
        try:
            filepath = model_without_extension + ".step"
            shutil.copy2(filepath, model_folder_path)
            copied_at_least_one = True
        except:
            pass
        try:
            filepath = model_without_extension + ".stp"
            shutil.copy2(filepath, model_folder_path)
            copied_at_least_one = True
        except:
            pass
        try:
            filepath = model_without_extension + ".igs"
            shutil.copy2(filepath, model_folder_path)
            copied_at_least_one = True
        except:
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
                new_model_path = "${KIPRJMOD}/" + "shapes3D/" + model_name
                # if enclosed with doublequotes, enclose line_new also
                if "\"" in mod:
                    new_model_path = "\"" + new_model_path + "\""
                line_new = line.replace(mod, new_model_path)
                pass
        out_file.append(line_new)
    # write
    logger.info("Writing pcb layout file")
    if alt_files:
        filename = filename + "_alt"
    with open(filename, "w") as f:
        f.writelines(out_file)
    pass


def main():
    board = pcbnew.LoadBoard('archive_test_project.kicad_pcb')

    #board = pcbnew.LoadBoard('D:\\Mitja\Plate\\Kicad_libs\\action_plugins\\archive_project\\USB breakout Test\\USB_Breakout_v3.0.kicad_pcb')
    
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

    file_handler = logging.FileHandler(filename='archive_project.log')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]
    # handlers = [file_handler]

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=handlers,
                        filemode='w'
                        )

    logger = logging.getLogger(__name__)
    logger.info("Archive plugin started in standalone mode")

    main()
