import glob
import itertools as it
import os

import parmed as pmd
from pkg_resources import resource_filename
import pytest

from foyer import Forcefield
from foyer.tests.utils import atomtype

GAFF = Forcefield(name='gaff')

GAFF_TESTFILES_DIR = resource_filename('foyer', 'gaff_validation')

class TestGAFF(object):

    @pytest.fixture(autouse=True)
    def initdir(self, tmpdir):
        tmpdir.chdir()

    top_files = glob.glob(os.path.join(GAFF_TESTFILES_DIR, '*/*.top'))
    mol2_files = glob.glob(os.path.join(GAFF_TESTFILES_DIR, '*/*.mol2'))

    # Please update this file if you implement atom typing for a test case.
    # You can automatically update the files by running the below function
    # `find_correctly_implemented`.
    implemented_tests_path = os.path.join(os.path.dirname(__file__),
                                          'implemented_gaff_tests.txt')
    with open(implemented_tests_path) as f:
        correctly_implemented = [line.strip() for line in f]

    def find_correctly_implemented(self):
        with open(self.implemented_tests_path, 'a') as fh:
            for mol_path in it.chain(self.top_files, self.mol2_files):
                _, mol_file = os.path.split(mol_path)
                mol_name, ext = os.path.splitext(mol_file)
                try:
                   self.test_atomtyping(mol_name)
                except Exception as e:
                    print(e)
                    continue
                else:
                    if mol_name not in self.correctly_implemented:
                        fh.write('{}\n'.format(mol_name))

    @pytest.mark.parametrize('mol_name', correctly_implemented)
    def test_atomtyping(self, mol_name, testfiles_dir=GAFF_TESTFILES_DIR):
        files = glob.glob(os.path.join(testfiles_dir, mol_name, '*'))
        for mol_file in files:
            full_path, ext = os.path.splitext(mol_file)
            if ext == '.top':
                mobley_name = os.path.splitext(os.path.split(mol_file)[-1])[0]
                top_filename = '{}.top'.format(mobley_name)
                gro_filename = '{}.gro'.format(mobley_name)
                top_path = os.path.join(testfiles_dir, mol_name, top_filename)
                gro_path = os.path.join(testfiles_dir, mol_name, gro_filename)
                structure = pmd.load_file(top_path, xyz=gro_path, parametrize=False)
            elif ext == '.mol2':
                mol2_path = os.path.join(testfiles_dir, mol_name, mol_file)
                structure = pmd.load_file(mol2_path, structure=True)
        atomtype(structure, GAFF)

    def test_full_parametrization(self):
        top = os.path.join(GAFF_TESTFILES_DIR, 'benzene/mobley_3053621.top')
        gro = os.path.join(GAFF_TESTFILES_DIR, 'benzene/mobley_3053621.gro')
        structure = pmd.load_file(top, xyz=gro)
        parametrized = GAFF.apply(structure)

        assert sum((1 for at in parametrized.atoms if at.type == 'ca')) == 6
        assert sum((1 for at in parametrized.atoms if at.type == 'ha')) == 6
        assert len(parametrized.bonds) == 12
        assert all(x.type for x in parametrized.bonds)
        assert len(parametrized.angles) == 18
        assert all(x.type for x in parametrized.angles)
        assert len(parametrized.dihedrals) == 30
        assert all(x.type for x in parametrized.dihedrals)



if __name__ == '__main__':
    TestGAFF().find_correctly_implemented()
