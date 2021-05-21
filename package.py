from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree
import zipfile
import tempfile
from zlib import adler32
import os

MANIFEST_NAME = "PackageContents.xml"

def parse_package_contents(root):
    # type: (FileObject) -> dict
    name = root.attrib["Name"]
    description = root.attrib["Description"]
    version = root.attrib["AppVersion"]
    product = root.attrib["AutodeskProduct"]
    product_code = root.attrib["ProductCode"]
    upgrade_code = root.attrib["UpgradeCode"]
    components = []
    for child in root:
        if child.tag == "RuntimeRequirements":
            requirements = parse_requirements(child)
        elif child.tag == "Components":
            components.append(parse_components(child))
        elif child.tag == "CompanyDetails":
            continue
        else:
            raise ValueError("Unexpected value: %s" % child.tag)

    return dict(
        name=name,
        version=version,
        description=description,
        product=product,
        product_code=product_code,
        upgrade_code=upgrade_code,
        requirements=requirements,
        components=components

    )    

def parse_requirements(element):
    # type: (element) -> dict
    """Parse a package requirements element"""

    # we strip whitespace for packages use '3ds Max' instead of '3dsMax'
    platform = tuple(
        ["".join(e.split()) for e in element.attrib["Platform"].split("|")]
    )
    os = tuple([os_.lower() for os_ in element.attrib["OS"].split("|")])

    series_min = element.attrib["SeriesMin"]
    series_max = element.attrib["SeriesMax"]

    # handle LT in versions for maya lt, maybe autocad LT?
    if series_min.endswith("LT"):
        series_min = series_min[:-2]
        platform = tuple([p + "LT" for p in platform])
    if series_max.endswith("LT"):
        series_max = series_max[:-2]

    return dict(
        platform=platform, os=os, series_min=series_min, series_max=series_max
    )


def parse_component_entry(element):
    module_name = element.attrib["ModuleName"]
    return dict(
        module_name=module_name, 
    )

def parse_components(element):
    # type: (element) -> dict
    """Parse a package Components element"""

    description = element.attrib["Description"]
    requirements = dict()
    componentEntries = []
    for child in element:
        if child.tag == "RuntimeRequirements":
            requirements = parse_requirements(child)
        elif child.tag == "ComponentEntry":
            componentEntries.append(parse_component_entry(child))
        else:
            raise ValueError("Unexpected value: %s" % child.tag)

    return dict(
        description=description, 
        component_entries=componentEntries,
        requirements=requirements,
    )

def package_data_from_manifest(file_path):
    """Return a package from a folder path."""
    # type: (Path) -> Path
    root = None
    if file_path.exists():
        with open(file_path, "r") as file_obj:
            try:
                xml_tree = ElementTree.parse(file_obj)
                root = xml_tree.getroot()
            except ElementTree.ParseError:
                # some xmls are encoded utf-8-sig
                file_obj.close()
                file_obj = open(file_path, encoding="utf-8-sig")
                xml_tree = ElementTree.parse(file_obj)
                root = xml_tree.getroot()                
    else:
        raise ValueError("Not a valid package folder: %s" % file_path)
    return parse_package_contents(root)


def main():
    manifest = Path(MANIFEST_NAME)
    additional_file_list = [
        "./scripts/max_usd_examples/usd_export_utils.py",
        "./scripts/max_usd_examples/usd_callbacks.py",
        "./scripts/max_usd_examples/usd_asset_params.ms",
        "./scripts/max_usd_examples/usd_export_common_params.ms",
        "./scripts/max_usd_examples/usd_export_modifier_params.ms",
        "./scripts/max_usd_examples/usd_scene_export_params.ms",
        "./scripts/max_usd_examples/usd_export_with_assets.py",
        "./scripts/max_usd_examples/instances_util.py",
        "./scripts/max_usd_examples/usdMakeFileVariantModelAsset.py",
        "README.md"
    ]
    if not manifest.exists():
        return "Missing manifest"
    manifest_data = package_data_from_manifest(manifest)
    series_min = manifest_data['requirements']['series_min']
    series_max = manifest_data['requirements']['series_max']
    for max_version in range(int(series_min), int(series_max)+1):
        file_name = f"max-{max_version}-usd-examples"
        zip_file_name = file_name + '.mzp'
        component_entries = []
        for component in manifest_data['components']:
            for component_entry in component['component_entries']:
                component_entries.append(component_entry['module_name'])
        with ZipFile(zip_file_name, 'w') as myzip:
            with open("mzp.run", 'r') as str_file:
                data = str_file.read()
                myzip.writestr("mzp.run", data.replace("{max_version}", str(max_version)), compress_type=None, compresslevel=None)
            with open("mzp_init.ms", 'r') as str_file:
                data = str_file.read()
                myzip.writestr("mzp_init.ms", data.replace("{max_version}", str(max_version)), compress_type=None, compresslevel=None)
            manifest_arcname = Path("./" + file_name + "/") / manifest            
            # myzip.write(manifest, manifest_arcname)
            xml_tree = ElementTree.parse(manifest)
            xml_root = xml_tree.getroot()
            for element in (xml_root.findall(".//RuntimeRequirements")):
                element.set('SeriesMin', str(max_version))
                element.set('SeriesMax', str(max_version))
            xml_str = ElementTree.tostring(xml_tree.getroot())
            myzip.writestr(str(manifest_arcname), xml_str)
            for entry in (component_entries + additional_file_list):
                _file = Path(entry)
                arcname = Path("./" + file_name + "/") / _file
                print(arcname)
                if _file.exists():
                    myzip.write(entry, arcname=str(arcname))
                else:
                    print(f"Missing: {entry}")
if __name__ == "__main__":
    main()