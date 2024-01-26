import logging # https://docs.python.org/3/library/logging.html
mylog = logging.getLogger().getChild('lib.classes.dev_proj_dir')

from dataclasses import dataclass, field # https://docs.python.org/3/library/dataclasses.html
from datetime import datetime # https://docs.python.org/3/library/datetime.html
from typing import ClassVar # https://docs.python.org/3/library/typing.html

import os # https://docs.python.org/3/library/os.html
import re # https://docs.python.org/3/library/re.html



@dataclass
class _DevelopmentNonDirectoryObjectStatistics:
    ''' Development non-directory object (e.g. module, class, function) statistics class. '''
    classes: int = 0
    functions: int = 0
    lines: int = 0
    characters: int = 0


@dataclass
class _DevelopmentDirectoryObjectStatistics(_DevelopmentNonDirectoryObjectStatistics):
    ''' Development directory object statistics class. '''
    directories: int = 0
    modules: int = 0



@dataclass
class _DevelopmentObject:
    ''' Development object class. '''
    relative_path: str = None
    basename: str = None
    type: str = None # e.g. directory, module, class, function
    contents: list = field(default_factory=list)



@dataclass
class _DevelopmentObjectDirectory(_DevelopmentObject):
    ''' Development directory class. '''
    statistics: _DevelopmentDirectoryObjectStatistics = field(default_factory=_DevelopmentDirectoryObjectStatistics)


    def _update_inventory_subdir(self, pathname: str, directories_excluded: list = [], module_extensions_included: list = []) -> None:
        ''' Update statistics information given subdirectory contents, including specified module extensions and excluding specified directories. '''

        # Get information for subdirectory, including specified module extensions and excluding specified directories.
        subdir_inventory = _DevelopmentObjectDirectory()
        subdir_inventory._get_inventory(pathname,
                                        directories_excluded,
                                        module_extensions_included,
                                        '.'.join([self.relative_path, os.path.basename(pathname)])
        )

        # Increment directory's subdirectory count.
        self.statistics.directories += 1

        # Update directory statistics (i.e. include subdirectory statistics in directory statistics).
        self.statistics.directories += subdir_inventory.statistics.directories
        self.statistics.modules += subdir_inventory.statistics.modules
        self.statistics.classes += subdir_inventory.statistics.classes
        self.statistics.functions += subdir_inventory.statistics.functions
        self.statistics.lines += subdir_inventory.statistics.lines
        self.statistics.characters += subdir_inventory.statistics.characters

        # Include subdirectory in directory content collection.
        self.contents.append(subdir_inventory)


    def _update_inventory_mod(self, pathname: str) -> None:
        ''' Update statistics information given module, including it's classes and functions. '''

        # Set identifying information for module object.
        mod_inventory = _DevelopmentObjectNonDirectory()
        mod_inventory.basename = os.path.basename(pathname)
        mod_inventory.relative_path = '.'.join([self.relative_path, os.path.splitext(mod_inventory.basename)[0]])
        mod_inventory.type = 'mod'
        mod_inventory._get_inventory_mod(pathname)

        # Increment directory's module count.
        self.statistics.modules += 1

        # Update directory statistics (i.e. include module statistics in directory statistics).
        self.statistics.classes += mod_inventory.statistics.classes
        self.statistics.functions += mod_inventory.statistics.functions
        self.statistics.lines += mod_inventory.statistics.lines
        self.statistics.characters += mod_inventory.statistics.characters

        # Include subdirectory in directory content collection
        self.contents.append(mod_inventory)


    def _get_inventory(self, dirpathname: str, directories_excluded: list = [], module_extensions_included: list = [], relative_path: str = '') -> None:
        ''' Get directory information and statistics, excluding specified directories and including specified file extensions. '''
        
        # Set identifying information for directory object.
        self.relative_path = relative_path
        self.basename = os.path.basename(dirpathname)
        self.type = 'dir'

        # Check objects in directory.
        for obj in os.listdir(dirpathname):
            
            # Get fully qualified path for contained subdirectory object.
            obj_pathname = os.path.join(dirpathname, obj)

            # Check if object is directory, not in excluded directories list.
            if os.path.isdir(obj_pathname) and (obj not in directories_excluded):
                self._update_inventory_subdir(obj_pathname,
                                              directories_excluded,
                                              module_extensions_included
                )

            # Check if object is file with extension in module extensions list.
            elif os.path.isfile(obj_pathname) and (os.path.splitext(obj)[1] in module_extensions_included):
                self._update_inventory_mod(obj_pathname)

            else: # Ignore object because either 1) an excluded directory; or, 2) a file with extension not in included module extensions list.
                pass



@dataclass
class _DevelopmentObjectNonDirectory(_DevelopmentObject):
    ''' Development non-directory object (e.g. module, class, function) class. '''
    # Define class attributes.
    statistics: _DevelopmentNonDirectoryObjectStatistics = field(default_factory=_DevelopmentNonDirectoryObjectStatistics)

    # Define class variables to avoid setting for each instance and related methods, especially loops.
    # Compile regular expression.
    _REGEX_PTN_PYTHON_FNC_CLS: ClassVar[re.Pattern] = re.compile(r'^(?P<indent>[ ]*)(?P<type>(?:def|class))[ ](?P<name>.*?(?=(?:\(|:)))')
    _REGEX_PTN_PYTHON_LINE_INDENT: ClassVar[re.Pattern] = re.compile(r'^(?P<indent>[ ]*)(?P<code>\S)')


    def _get_fnc_cls_content(self, indent: str, remaining_content: list[str]) -> dict:
        ''' Get function or class content. '''

        # Get function or class indent space count.
        indent_spaces_count = len(indent)

        # Check remaining content lines for class and function definitions
        # with fewer or same indentation. If found, stop.
        fnc_cls_content = None
        for line_index in range(1, len(remaining_content)):
            match_result = re.match(self._REGEX_PTN_PYTHON_LINE_INDENT, remaining_content[line_index])
            
            if (match_result is not None) and (len(match_result.group('indent')) <= indent_spaces_count):
                fnc_cls_content = remaining_content[:line_index]
                break
        
        # If no class or function definition found, use remaining content.
        if fnc_cls_content is None:
            fnc_cls_content = remaining_content
        
        return { 'content': fnc_cls_content, 'next_line_increment': line_index }


    def _update_inventory_fnc_cls(self, content: list[str]) -> None:
        ''' Update statistics information given module, class, or function object, including embedded classes and functions. '''

        # Update statistics given module, class, or function content, including embedded classes and functions.
        self.statistics.lines = len(content)
        self.statistics.characters = len(''.join(content))

        next_line_to_check = 0 # Skip lines already found in class and function definitions.

        # Check content lines for class and function definitions.
        for line_index in range(1, len(content)):
            if line_index >= next_line_to_check:
                sub_fnc_cls_def = re.match(self._REGEX_PTN_PYTHON_FNC_CLS, content[line_index])

                if sub_fnc_cls_def is not None:
                    # Set identifying information for embedded class or function object.
                    sub_fnc_cls_inventory = _DevelopmentObjectNonDirectory()
                    sub_fnc_cls_inventory.basename = sub_fnc_cls_def.group('name')
                    sub_fnc_cls_inventory.relative_path = '.'.join([self.relative_path, sub_fnc_cls_inventory.basename])
                    if sub_fnc_cls_def.group('type') == 'class':
                        sub_fnc_cls_inventory.type = 'cls'
                    elif sub_fnc_cls_def.group('type') == 'def':
                        sub_fnc_cls_inventory.type = 'fnc'
                    else:
                        raise ValueError(f'Invalid function or class object type: {sub_fnc_cls_def.group('type')} in {self.relative_path}')

                    # Get embedded function or class content, including it's embedded classes and functions.
                    result = sub_fnc_cls_inventory._get_fnc_cls_content(sub_fnc_cls_def.group('indent'), content[line_index:])
                    sub_fnc_cls_content = result['content']
                    next_line_to_check = line_index + result['next_line_increment']

                    # Update module, function, or class statistics to include embedded class or function.
                    if sub_fnc_cls_inventory.type == 'cls':
                        self.statistics.classes += 1
                    else: # sub_fnc_cls_inventory.type == 'fnc':
                        self.statistics.functions += 1
                    
                    # Set embedded class or function statistics, including embedded classes and functions.
                    sub_fnc_cls_inventory._update_inventory_fnc_cls(sub_fnc_cls_content)

                    # Update module, function, or class statistics to include embedded classes and functions.
                    self.statistics.classes += sub_fnc_cls_inventory.statistics.classes
                    self.statistics.functions += sub_fnc_cls_inventory.statistics.functions

                    # Include embedded class or function in class or function content collection
                    self.contents.append(sub_fnc_cls_inventory)


    def _get_inventory_mod(self, pathname) -> None:
        ''' Get module information and statistics, including embedded classes and functions. '''
        
        # Get module content.
        with open(pathname, mode='r', encoding='UTF-8') as f:
            mod_content = f.readlines()
            f.close()

        # Set module statistics, including embedded classes and functions.
        self._update_inventory_fnc_cls(mod_content)



@dataclass
class DevelopmentProjectDirectory(_DevelopmentObjectDirectory):
    ''' Class for development project directories containing all related directories, modules, classes, and functions. '''
    dirpathname: str = None
    directories_excluded: list = field(default_factory=list)
    module_extensions_included: list = field(default_factory=list)


    def save_development_inventory_report(self) -> None:
        ''' Get specified project directory information and statistics, excluding specified directories and including specified file extensions. '''
        self._get_inventory(self.dirpathname, self.directories_excluded, self.module_extensions_included)
        self._save_inventory_rpt()

        
    def _get_object_inventory_report(self, object_inventory: _DevelopmentObjectDirectory | _DevelopmentObjectNonDirectory, indent_level: int = 0) -> str:
        ''' Get object inventory summary report. '''

        # Set indent string.
        indent_str = '--' * indent_level

        # Add object information summary.
        rpt: str = (
            f'| {indent_str} {object_inventory.basename} '
            f'| {object_inventory.type} '
        )
        if object_inventory.type == 'dir':
            rpt += (
                f'| {object_inventory.statistics.directories:,d} '
                f'| {object_inventory.statistics.modules:,d} '
            )
        else:
            rpt += (
                f'| {0:,d} '
                f'| {0:,d} '
            )
        rpt += (
            f'| {object_inventory.statistics.classes:,d} '
            f'| {object_inventory.statistics.functions:,d} '
            f'| {object_inventory.statistics.lines:,d} '
            f'| {object_inventory.statistics.characters:,d} '
            '|\n'
        )

        for subobj_inventory in object_inventory.contents:
            # Add object information summary.
            rpt += self._get_object_inventory_report(subobj_inventory, indent_level + 1)

        return rpt


    def _save_inventory_rpt(self) -> None:
        ''' Save project directory inventory report. '''

        # Get output filename name.
        now = datetime.now()
        rpt_filename = self.basename + '-' + now.strftime('%Y%m%d%H%M%S') + '.md'
        rpt_filepathname = os.path.join(self.dirpathname, rpt_filename)

        # Set report header.
        rpt = (
            f'\n## Directory Report for {self.basename}\n'
            f'( {self.dirpathname} )<br/>\n'
            f'as of {now.isoformat()}<br/>\n'
            '\n'
            '| name | type |  dirs  |  mods  |  clss  |  fncs  | lines  | chars  |\n'
            '| :--- | :--: | -----: | -----: | -----: | -----: | -----: | -----: |\n'
            )

        # Add project directory information summary.
        rpt += (
            f'| {self.basename} '
            f'| {self.type} '
            f'| {self.statistics.directories:,d} '
            f'| {self.statistics.modules:,d} '
            f'| {self.statistics.classes:,d} '
            f'| {self.statistics.functions:,d} '
            f'| {self.statistics.lines:,d} '
            f'| {self.statistics.characters:,d} '
            '|\n'
        )

        for subobj_inventory in self.contents:
            # Add object inventory summary.
            rpt += self._get_object_inventory_report(subobj_inventory, 1)

        # Save report as new markdown document.
        with open(rpt_filepathname, mode='x', encoding='UTF-8') as f:
            f.write(rpt)
            f.close()

        return rpt