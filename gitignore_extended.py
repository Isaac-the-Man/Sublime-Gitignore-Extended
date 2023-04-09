'''
Sublime Text package for composing .gitignore using the publicliy maintained templates.
All templates are fetched from https://github.com/github/gitignore

Author: Yu-Kai "Steven" Wang
Github: Isaac-the-Man
'''
import sublime
import sublime_plugin
from itertools import chain
from glob import iglob
import os


def load_default_templates():
	'''
	Read .gitignores from the github repo
	'''
	# intialize lists
	ignores_name = []
	ignores_path = []
	# read default templates
	pattern = [
		'*.gitignore',
		os.path.join('Global', '*.gitignore'),
		os.path.join('community', '*.gitignore'),
		os.path.join('community', '**', '*.gitignore'),
	]
	root = os.path.join(sublime.packages_path(), 'Sublime-Gitignore-Extended', 'gitignore')
	for fname in chain(*(iglob(os.path.join(root, ptrn)) for ptrn in pattern)):
		name = os.path.splitext(os.path.basename(fname))[0]
		tag = os.path.dirname(os.path.relpath(fname, root)).split(os.sep)
		if len(tag) > 1:
			name = '{} ({})'.format(name, ' | '.join(tag))
		ignores_name.append(name)
		ignores_path.append(fname)
	return ignores_name, ignores_path


def load_custom_templates():
	'''
	Read custom .gitignores templates
	'''
	# read settings
	settings = sublime.load_settings('gitignore_extended.sublime-settings')
	# intialize lists
	ignores_name = []
	ignores_path = []
	# read custom templates
	custom_path = os.path.join(sublime.packages_path(), 'User',
			settings.get('custom_template_path', 'CustomGitignoreTemplates'))
	os.makedirs(custom_path, exist_ok=True)
	for fname in iglob(os.path.join(custom_path, '*.gitignore')):
		name = '{} (custom)'.format(os.path.splitext(os.path.basename(fname))[0])
		ignores_name.append(name)
		ignores_path.append(fname)
	return ignores_name, ignores_path


def load_templates():
	'''
	Returns a list of templates
	'''
	# intialize lists
	ignores_name = []
	ignores_path = []
	# load and merge default/custom templates
	names, paths = load_default_templates()
	ignores_name.extend(names)
	ignores_path.extend(paths)
	names, paths = load_custom_templates()
	ignores_name.extend(names)
	ignores_path.extend(paths)

	return ignores_name, ignores_path


class saveGitignoreCommand(sublime_plugin.TextCommand):
	'''
	Write content to .gitignore
	'''
	def run(self, edit, **kwargs):
		self.view.insert(edit, 0, kwargs['content'])


class ComposeGitignoreCommand(sublime_plugin.WindowCommand):
	'''
	Compose new .gitignore from template.
	'''
	compositions = set()


	def __init__(self, *args, **kwargs):
		'''
		Fetch available .gitignore templates
		'''
		super().__init__(*args, **kwargs)
		# load templates
		self.ignores_name, self.ignores_path = load_templates()
		self.ignores_name.insert(0, 'done')


	def run(self):
		'''
		Start selection
		'''
		# load templates
		self.ignores_name, self.ignores_path = load_templates()
		self.ignores_name.insert(0, 'done')
		# clear previous session
		self.compositions.clear()
		# select panel
		self._select()


	def _select(self, idx=None):
		'''
		Recurive selection
		'''
		if idx == -1:
			# dismissed
			return
		elif idx == 0:
			# done
			self._compose()
		else:
			if idx is not None:
				# second+ selection
				self.compositions.add(idx)
			# next selection
			self.window.show_quick_panel(
				self.ignores_name,
				on_select=self._select)


	def _read_file(self, path):
		'''
		Read content of .gitignore
		'''
		with open(path, 'r', encoding='utf-8') as f:
			content = f.read()
		return content


	def _compose(self):
		'''
		Concatenate .gitignore templates
		'''
		# create new file
		view = self.window.new_file()
		view.set_name('.gitignore')
		view.assign_syntax(sublime.find_syntax_by_name('Git Ignore')[0])	# assigning a Syntax object here since setting syntax name in View.new_file() seems to raise an error.
		# compose .gitignore from template
		buffer = []
		for idx in self.compositions:
			buffer.append(
				'### {} ### \n\n'.format(self.ignores_name[idx]) +
				self._read_file(self.ignores_path[idx - 1]))
		buffer = '\n\n'.join(buffer)
		# inject composed content to file
		view.run_command('save_gitignore', {'content': buffer})


class NewCustomGitignoreTemplateCommand(sublime_plugin.WindowCommand):
	'''
	Create a new custom .gitignore template
	'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.settings = sublime.load_settings('gitignore_extended.sublime-settings')
		# check for custom template folder
		self.custom_path = os.path.join(sublime.packages_path(), 'User',
				self.settings.get('custom_template_path', 'CustomGitignoreTemplates'))


	def run(self):
		self.window.show_input_panel('File Name: ', 'my_template', 
				self._new_template, None, None)


	def _new_template(self, name):
		# create empty file
		filename = '{}.gitignore'.format(name)
		with open(os.path.join(self.custom_path, filename), 'w') as f:
			f.write('# custom .gitignore template #')			
		view = self.window.open_file(os.path.join(self.custom_path, filename))


class EditCustomGitignoreTemplateCommand(sublime_plugin.WindowCommand):
	'''
	Create a new custom .gitignore template
	'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.settings = sublime.load_settings('gitignore_extended.sublime-settings')
		# check for custom template folder
		self.custom_path = os.path.join(sublime.packages_path(), 'User',
				self.settings.get('custom_template_path', 'CustomGitignoreTemplates'))
		# load custom templates
		self.ignores_name, self.ignores_path = load_custom_templates()


	def run(self):
		'''
		Start selection
		'''
		# load custom templates
		self.ignores_name, self.ignores_path = load_custom_templates()
		# select file
		self.window.show_quick_panel(self.ignores_name, 
				on_select=self._select,
				on_highlight=self._preview)


	def _select(self, idx):
		'''
		Open selected template
		'''
		if idx == -1:
			# close preview and dismiss
			view = self.window.active_view()
			if self.window.get_view_index(view)[1] == -1:
				view.close()
			return
		# open file as tab
		self.window.open_file(self.ignores_path[idx])


	def _preview(self, idx):
		'''
		Preview selected template
		'''
		self.window.open_file(self.ignores_path[idx], sublime.TRANSIENT)


class DeleteCustomGitignoreTemplateCommand(sublime_plugin.WindowCommand):
	'''
	Delete a custom .gitignore template
	'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.settings = sublime.load_settings('gitignore_extended.sublime-settings')
		# check for custom template folder
		self.custom_path = os.path.join(sublime.packages_path(), 'User',
				self.settings.get('custom_template_path', 'CustomGitignoreTemplates'))
		# load custom templates
		self.ignores_name, self.ignores_path = load_custom_templates()


	def run(self):
		'''
		Start selection
		'''
		# load custom templates
		self.ignores_name, self.ignores_path = load_custom_templates()
		# select file
		self.window.show_quick_panel(self.ignores_name, 
				on_select=self._select,
				on_highlight=self._preview)


	def _select(self, idx):
		'''
		Delete selected template
		'''
		if idx >= 0:
			# remove file
			os.remove(self.ignores_path[idx])
		# close preview and dismiss
		view = self.window.active_view()
		if self.window.get_view_index(view)[1] == -1:
			view.close()


	def _preview(self, idx):
		'''
		Preview selected template
		'''
		self.window.open_file(self.ignores_path[idx], sublime.TRANSIENT)