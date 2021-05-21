(
local script_file = getSourceFileName()
local script_path = substituteString (getFilenamePath(script_file)) "\\" "/"
python.execute(
    "import sys\n" +
    "if not '" + script_path + "' in sys.path:\n" +
    "    sys.path.append('" + script_path + "')")
)