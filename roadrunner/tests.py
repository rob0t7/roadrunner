import os, re, shutil, sys
import zc.buildout.tests
import zc.buildout.testing

import unittest
from zope.testing import doctest, renormalizing
from roadrunner.recipe import RoadrunnerPloneRecipe, RoadrunnerRecipe

os_path_sep = os.path.sep
if os_path_sep == '\\':
    os_path_sep *= 2

def dirname(d, level=1):
    if level == 0:
        return d
    return dirname(os.path.dirname(d), level-1)

def setUp(test):
    zc.buildout.tests.easy_install_SetUp(test)

from mocker import MockerTestCase

# from zc.recipe.egg.egg import Scripts
class ScriptsMock(zc.recipe.egg.egg.Scripts):
    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options
        
    def install(self, *args, **kwargs):
        return []

def fake_setup_layer(layer, setup_layers):
    setup_layers[layer] = True
    
class RunnerTests(MockerTestCase):
    def test_preload_plone(self):
        from roadrunner import runner

        setup_plone = self.mocker.replace('roadrunner.runner.setup_plone')
        setup_plone()
        self.mocker.result(None)

        setup_layer = self.mocker.replace('roadrunner.testrunner.setup_layer')
        setup_layer(None, {})
        self.mocker.call(fake_setup_layer)
        
        self.mocker.replay()
        
        layers = runner.preload_plone()
        self.assertEquals(layers, {})

class RoadrunnnerRecipeTests(MockerTestCase):
    def test_basic_recipe(self):
        buildout = dict(
            buildout={
                'eggs-directory': '',
                'directory': '/fake',
            },
            instance = {
                'location': '/fake/parts/instance',
                'eggs': 'egg1\negg2',
                'zope2-location': '/zope2/location',
            },
        )
        options = {
            'eggs': 'egg1\negg2'
        }
        # self.mocker.replace('os.path.exists')().result(True)
        # self.mocker.replace('os.mkdir')().result(True)
        
        # mock out file reading
        orig_file = __builtins__['file']
        f = self.mocker.mock()
        __builtins__['file'] = f
        my_file = self.mocker.mock()
        my_file.read()
        self.mocker.result('/fake/parts/instance')
        self.expect(f('/fake/parts/roadrunner/etc/zope.conf'))
        self.mocker.result(my_file)
        
        # mock out file reading
        write_file = self.mocker.mock()
        write_file.write('/fake/parts/roadrunner')
        f('/fake/parts/roadrunner/etc/zope.conf', 'w')
        self.mocker.result(write_file)
        ct = self.mocker.replace('shutil.copytree')
        ct(buildout['instance']['location'], '/fake/parts/roadrunner')
        self.mocker.result(True)
        
        mock_recipe()
        self.mocker.replay()
        
        recipe = RoadrunnerPloneRecipe(buildout, 'roadrunner', options)
        self.assertEquals(recipe.install(), ['/fake/parts/roadrunner'])
        unmock_recipe()
    
    def test_packages_under_test(self):
        # self.instance_part = buildout[options.get('zope2-instance', 'instance')]
        # self.part_dir = self.buildout['buildout']['directory'] + "/parts/" + self.name
        # self.packages_under_test = options.get('packages-under-test', '').split()
        
        mock_recipe()
        buildout = {'buildout': {'directory': '/fake'}, 'instance': None}
        options = {'packages-under-test': 'package.*'}
        recipe = RoadrunnerPloneRecipe(buildout, 'roadrunner', options)
        self.assertEquals(recipe.is_package_under_test('/fake/eggs/package.foo'), True)
        self.assertEquals(recipe.is_package_under_test('/fake/eggs/other.foo'), False)

        unmock_recipe()

    def test_update(self):
        mock_recipe()
        buildout = {'buildout': {'directory': '/fake'}, 'instance': None}
        options = {'packages-under-test': 'package.*'}
        recipe = RoadrunnerPloneRecipe(buildout, 'roadrunner', options)
        recipe.install = self.mocker.mock()
        
        self.expect(recipe.install())
        self.mocker.replay()
        
        self.assertEquals(recipe.update(), None)
        unmock_recipe()

    def test_recipe_with_os_path_exists(self):
        buildout = dict(
            buildout={
                'eggs-directory': '',
                'directory': '/fake',
            },
            instance = {
                'location': '/fake/parts/instance',
                'eggs': 'egg1\negg2',
                'zope2-location': '/zope2/location',
            },
        )
        options = {
            'eggs': 'egg1\negg2'
        }
        
        # mock out parts directory existing and shutil call after it.
        # not important since the algorithm is just delete the directory if it exists
        os.path.exists = self.mocker.replace('os.path.exists')
        os.path.exists('/fake/parts/roadrunner')
        self.mocker.result(True)
        shutil.rmtree = self.mocker.mock()
        self.expect(shutil.rmtree('/fake/parts/roadrunner'))

        # mock out file reading
        orig_file = __builtins__['file']
        f = self.mocker.mock()
        __builtins__['file'] = f
        my_file = self.mocker.mock()
        my_file.read()
        self.mocker.result('/fake/parts/instance')
        self.expect(f('/fake/parts/roadrunner/etc/zope.conf'))
        self.mocker.result(my_file)

        # mock out file reading
        write_file = self.mocker.mock()
        write_file.write('/fake/parts/roadrunner')
        f('/fake/parts/roadrunner/etc/zope.conf', 'w')
        self.mocker.result(write_file)
        ct = self.mocker.replace('shutil.copytree')
        ct(buildout['instance']['location'], '/fake/parts/roadrunner')
        self.mocker.result(True)

        mock_recipe()
        self.mocker.replay()

        recipe = RoadrunnerPloneRecipe(buildout, 'roadrunner', options)
        self.assertEquals(recipe.install(), ['/fake/parts/roadrunner'])
        unmock_recipe()

    def test_with_packages_in_package_includes(self):
        buildout = dict(
            buildout={
                'eggs-directory': '',
                'directory': '/fake',
            },
            instance = {
                'location': '/fake/parts/instance',
                'eggs': 'egg1\negg2',
                'zope2-location': '/zope2/location',
            },
        )
        options = {
            'eggs': 'egg1\negg2'
        }

        #mock out the files returned from os.walk in ../etc/package-includes
        os.walk = self.mocker.mock()
        self.expect(os.walk('/fake/parts/roadrunner/etc/package-includes')).result([('dir','2',['filename1'])])
        RoadrunnerPloneRecipe.is_package_under_test = self.mocker.mock()
        self.expect(RoadrunnerPloneRecipe.is_package_under_test('filename1')).result(True)
        os.remove = self.mocker.mock()
        self.expect(os.remove('dir/filename1'))

        # mock out file reading
        orig_file = __builtins__['file']
        f = self.mocker.mock()
        __builtins__['file'] = f
        my_file = self.mocker.mock()
        my_file.read()
        self.mocker.result('/fake/parts/instance')
        self.expect(f('/fake/parts/roadrunner/etc/zope.conf'))
        self.mocker.result(my_file)

        # mock out file reading
        write_file = self.mocker.mock()
        write_file.write('/fake/parts/roadrunner')
        f('/fake/parts/roadrunner/etc/zope.conf', 'w')
        self.mocker.result(write_file)
        ct = self.mocker.replace('shutil.copytree')
        ct(buildout['instance']['location'], '/fake/parts/roadrunner')
        self.mocker.result(True)

        mock_recipe()
        self.mocker.replay()

        recipe = RoadrunnerPloneRecipe(buildout, 'roadrunner', options)
        self.assertEquals(recipe.install(), ['/fake/parts/roadrunner'])
        unmock_recipe()


original_bases = None
def mock_recipe():
    from roadrunner.recipe import RoadrunnerPloneRecipe, RoadrunnerRecipe
    global original_bases
    original_bases = RoadrunnerRecipe.__bases__
    RoadrunnerRecipe.__bases__ = (ScriptsMock,)

def unmock_recipe():
    from roadrunner.recipe import RoadrunnerPloneRecipe, RoadrunnerRecipe
    RoadrunnerRecipe.__bases__ = original_bases

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
    
# def test_suite():
#     globs = dict(plone_buildout_cfg=plone_buildout_cfg)
#     suite = unittest.TestSuite()
#     # suite = unittest.TestSuite((
#     #     doctest.DocFileSuite(
#     #         'recipe.txt',
#     #         setUp=setUp, tearDown=zc.buildout.testing.buildoutTearDown,
#     #         globs=globs,
#     #         checker=renormalizing.RENormalizing([
#     #            zc.buildout.testing.normalize_path,
#     #            zc.buildout.testing.normalize_script,
#     #            zc.buildout.testing.normalize_egg_py,
#     #            zc.buildout.tests.normalize_bang,
#     #            (re.compile('zc.buildout(-\S+)?[.]egg(-link)?'),
#     #             'roadrunner'),
#     #            (re.compile('[-d]  setuptools-[^-]+-'), 'setuptools-X-')
#     #            ]),
#     #         # optionflags=doctest.ABORT_AFTER_FIRST_FAILURE,
#     #         ),
#     #     ))
#     suite.addTest(unittest.makeSuite(RoadrunnnerRecipeTests))
#     
#     return suite
    
plone_buildout_cfg = """\
[buildout]
parts=
#  zope2
  plone
  instance
  roadrunner
develop=
  src/test_package
  src/preloaded_package
  %s/..
eggs =
  elementtree
  test_package
  preloaded_package
  roadrunner
eggs-directory=/Users/jbb/.buildout/eggs
download-directory=/Users/jbb/.buildout/downloads
download-cache=/Users/jbb/.buildout/download-cache

[plone]
recipe = plone.recipe.plone

[zope2]
#recipe = plone.recipe.zope2install
#url = ${plone:zope2-url}
location=/Users/jbb/co/shared_plone3/parts/zope2

[instance]
recipe = plone.recipe.zope2instance
zope2-location = ${zope2:location}
user = admin:admin
http-address = 8080
eggs =
    ${buildout:eggs}
    ${plone:eggs}
products =
#    /Users/jbb/co/shared_plone3/parts/plone
    ${plone:products}

[roadrunner]
recipe = roadrunner:plone
#preload-packages = preloaded_package
package-under-test = test_package
""" % os.path.dirname(__file__)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
