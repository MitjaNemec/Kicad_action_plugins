import pcbnew
import os
import os.path
import shutil


def archive_symbols(board, alt_files=False):
    # get project name
    project_name = os.path.basename(board.GetFileName()).split(".")[0]
    cache_lib_name = project_name + "-cache.lib"
    
    # load system symbol library table
    sys_path = "C://Users//MitjaN//AppData//Roaming//kicad"
    #sys_path = pcbnew.GetKicadConfigPath()
    global_sym_lib_file_path = sys_path + "//sym-lib-table"
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
    proj_sym_lib_file_path = proj_path + "//sym-lib-table"
    with open(proj_sym_lib_file_path) as f:
        project_sym_lib_file = f.readlines()
    # append nicknames
    for line in project_sym_lib_file:
        nick_start = line.find("(name ")+6
        if nick_start >= 6:
            nick_stop = line.find(")", nick_start)
            nick = line[nick_start:nick_stop]
            nicknames.append(nick)

    # if there is already nickname cache but no actual cache-lib
    if "cache" not in nicknames and cache_lib_name not in unicode(project_sym_lib_file):
            # warn the user and quite
            pass
            return
    
    # if cache library is not on the list, put it there
    if cache_lib_name not in unicode(project_sym_lib_file):
        line = "(lib (name cache)(type Legacy)(uri ${KIPRJMOD}//" + cache_lib_name + ")(options "")(descr ""))"
        project_sym_lib_file.insert(1, line)
    
    # load cache library
    proj_cache_ling_path = proj_path + "//" + cache_lib_name
    with open(proj_cache_ling_path) as f:
        project_cache_file = f.readlines()

    # get list of symbols in cache library
    cache_symbols = []
    for line in project_cache_file:
        line_contents = line.split()
        if line_contents[0] == "DEF":
            cache_symbols.append(line_contents[1])

    # find all .sch files
    all_sch_files = []
    for root, directories, filenames in os.walk(proj_path):
        for filename in filenames:
            if filename.endswith(".sch"):
                all_sch_files.append(os.path.join(root, filename))

    # go through each .sch file
    for filename in all_sch_files:
        with open(filename) as f:
            sch_file = f.readlines()

        sch_file_out = []
        # find line starting with L and next word until colon mathes library nickname
        for line in sch_file:
            line_contents = line.split()
            if line_contents[0] == "L" and line_contents[1].split(":")[0] in nicknames:
                # replace colon with underscore
                new_name = line_contents[1].replace(":", "_")
                # make sure that the symbol is in cache and append cache nickname
                if new_name in cache_symbols:
                    line_contents[1] = "cache:" + new_name
                # join line back again
                new_line = ' '.join(line_contents)
                sch_file_out.append(new_line+"\n")
            else:
                sch_file_out.append(line)

        # write
        if alt_files:
            filename = filename + "_alt"
        with open(filename, "w") as f:
            f.writelines(sch_file_out)
            pass
    pass


def archive_3D_models(board):
    # load layout
    filename = board.GetFileName()
    with open(filename) as f:
        pcb_layout = f.readlines()

    # find all used models
    models = []
    for line in pcb_layout:
        index = line.find("(model")
        if index != -1:
            line_split = line.split()
            index = line_split.index("(model")
            model_path = line_split[index+1]
            model = os.path.basename(model_path)
            models.append(model.rsplit(".", 1)[0])
    models = list(set(models))

    model_library_path = os.getenv("KISYS3DMOD")
    # D:\Mitja\Plate\Kicad_libs\official_libs\Packages3D
    model_library_path = "D://Mitja//Plate//Kicad_libs//official_libs//Packages3D"

    # prepare folder for 3dmodels
    proj_path = os.path.dirname(os.path.abspath(board.GetFileName()))

    model_folder_path = proj_path + "//shapes3D"

    if not os.path.exists(model_folder_path):
        os.makedirs(model_folder_path)

    # go through the list of used model
    for model in models:
        for root, directories, filenames in os.walk(model_library_path):
            for filename in filenames:
                if model in filename and (filename.endswith(".wrl") or filename.endswith(".stp") or filename.endswith(".step")):
                    # copy file to model_folder_pah
                    shutil.copy2(root+"//"+filename, model_folder_path)

    # generate output file with project relative path
    out_file = []
    for line in pcb_layout:
        line_new = line
        index = line.find("(model")
        if index != -1:
            line_split = line.split("(model")
            for model in models:
                if model in line_split[1]:
                    model_path = " ${KIPRJMOD}/" + "shapes3D/" + model + ".wrl"
                    line_split_split = line_split[1].split()
                    line_split_split[0] = model_path
                    line_split[1] = " ".join(line_split_split)
                    line_new = "(model".join(line_split) + "\n"
        out_file.append(line_new)
    pass
    # write the file


def main():
    board = pcbnew.LoadBoard('En_mostic_test.kicad_pcb')

    archive_3D_models(board)

    archive_symbols(board, True)

    # kot only kicad related
    # os.getenv("KISYSMOD")
    # os.getenv("KISYS3DMOD")
    # os.getenv("KICAD_SYMBOL_DIR")
    # os.getenv("KIPRJMOD")


# for testing purposes only
if __name__ == "__main__":
    main()