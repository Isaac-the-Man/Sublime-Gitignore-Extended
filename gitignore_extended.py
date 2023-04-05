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
	pattern = [
		'*.gitignore',
		os.path.join('Global', '*.gitignore'),
		os.path.join('community', '*.gitignore'),
		os.path.join('community', '**', '*.gitignore'),
	]
	root = os.path.join(sublime.packages_path(), 'Sublime-Gitignore-Extended', 'gitignore')
	compositions = set()


	def __init__(self, *args, **kwargs):
		'''
		Fetch available .gitignore templates
		'''
		super().__init__(*args, **kwargs)
		# list .gitignore files
		self.ignores_name = ['done']
		self.ignores_path = []
		for fname in chain(*(iglob(os.path.join(self.root, ptrn)) for ptrn in self.pattern)):
			name = os.path.splitext(os.path.basename(fname))[0]
			# print(os.path.relpath(fname, self.root))
			tag = os.path.dirname(os.path.relpath(fname, self.root))
			if tag != '':
				name = '{} ({})'.format(name, tag)
			self.ignores_name.append(name)
			self.ignores_path.append(fname)


	def run(self):
		'''
		Start selection
		'''
		self.compositions.clear()
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
				on_select=self._select,
				selected_index=0)


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
