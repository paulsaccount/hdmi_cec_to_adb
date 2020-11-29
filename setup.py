from setuptools import setup, find_packages

with open('requirements.txt', 'r') as f:
    requires = f.read().splitlines()

with open('README.md', 'r') as f:
    readme = f.read()

setup(name='hdmi-cec-to-adb',
      version='0.1.0.dev6',
      author='Paul Pavlish',
      author_email='hello@paulpavlish.com',
      url='https://github.com/paulsaccount/hdmi_cec_to_adb',
      description='hdmi_cec_to_adb',
      packages=find_packages(exclude=['*tests*']),
      long_description=readme,
      long_description_content_type='text/markdown',
      install_requires=requires,
      entry_points={
          'console_scripts': [
              'start_hdmi_cec_monitor = hdmi_cec_to_adb.bin.start_hdmi_cec_monitor:main',
          ],
      },
      )
