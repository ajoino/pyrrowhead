from setuptools import setup
from pathlib import Path
from setuptools.command.install import install
from setuptools.command.develop import develop
from tkinter import Tk, ttk
from tkinter.filedialog import askdirectory

default_path = Path.home() / f'pyrrowhead-local-clouds/'

class PostDevelopCommand(develop):
    def run(self):
        develop.run(self)
        print(f'Choose directory for local cloud installations (default is: {default_path})')

class PostInstallCommand(install):
    def run(self):
        install.run(self)
        import typer
        import configparser

        Tk().withdraw()
        s = ttk.Style()
        s.theme_use('clam')
        filename = askdirectory(initialdir=Path.home(), title='Choose Arrowhead local cloud install directory')
        try:
            local_clouds_directory = Path(filename)
        except TypeError:
            local_clouds_directory = Path(typer.get_app_dir('pyrrowhead')) / 'local-clouds'
        typer.confirm(f'Local clouds will be installed in \'{local_clouds_directory.absolute()}\'')

        config_path = Path(typer.get_app_dir('pyrrowhead'))
        config = configparser.ConfigParser()
        try:
            with open(config_path / 'config.cfg', 'r') as config_file:
                config.read_file(config_file)
        except FileNotFoundError:
            print('Initializing config file...')
            config['pyrrowhead'] = {}
        config['local-clouds'] = {}

        config['pyrrowhead']['default-clouds-directory'] = str(local_clouds_directory)

        if local_clouds_directory.exists() and local_clouds_directory:
            for org_path in local_clouds_directory.iterdir():
                for cloud_path in org_path.iterdir():
                    config['local-clouds']['.'.join((str(cloud_path.name), str(org_path.name)))] = str(cloud_path.absolute())
        else:
            print(local_clouds_directory)
            local_clouds_directory.mkdir(parents=True)


        with open(config_path / 'config.cfg', 'w') as config_file:
            config.write(config_file)




if __name__ == '__main__':
    setup(
            cmdclass={
                'develop': PostDevelopCommand,
                'install': PostInstallCommand,
            }
    )