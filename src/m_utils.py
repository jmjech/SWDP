# coding=utf-8

#  THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
#  AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS
#  IS." THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES,
#  OFFICERS, EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED,
#  AS TO THE USEFULNESS OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE.
#  THEY ASSUME NO RESPONSIBILITY (1) FOR THE USE OF THE SOFTWARE AND
#  DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL SUPPORT TO USERS.

"""
#####################################################################
# Developed by Mike Jech, michael.jech@noaa.gov
# 
# National Oceanic and Atmospheric Administration (NOAA)
# Northeast Fisheries Science Center (NEFSC)
# Woods Hole, MA USA
#
# utilities to work with echoPype data
#
# This code was modified from mask.py written by Rick Towler
#####################################################################
"""

import numpy as np
import matplotlib
import xarray as xr
import pandas as pd
from pathlib import Path
import sys
from sys import exit
import json
import argparse
#from utils import parse_args


class arg_parser:
    '''
    Class to parse arguments passed from a command line
    '''

    def __init__(self):
        '''
        Initialize the dictionary that will be created with the arguments

        Input:
            arguments from argparse package
        
        '''
        self.pars_dict = {}


    def parse_args(self, args, showit=True):
        '''
        Parse the argument list and return a dictionary with the file names and paths
        This should include arguments from all programs that use the argparse for
        command line arguments.

        Input:
            command line arguments as argparse object
            optional - showit
                True will display/print-to-screen the resulting dictionary
                False will not display/print-to-screen the resulting dictionary

        Output:
            dictionary with output file directories as the keys and filenames
            as the values
        '''

        # set the EKmodel parameter
        pars_dict = parse_EKmodel(self, args)

        # set the output directory for the netCDF4 files
        pars_dict = parse_nc(self, args)

        # parse the file names and paths from the arguments
        pars_dict = pars_filenames(self, args)

        # get the metadata
        pars_dict = parse_metadata(self, args)

        if (args.jsonfile):
            # json file provided
            pars_dict = parse_json(self, args)

        if (showit):
            display_pars(self)

        return(pars_dict)


    def display_pars(self):
        '''
        print the parameters to the display

        Input:
            parameter dictionary

        Output:
            none
        '''
        for k, v in self.pars_dict.items():
            print('{}'.format(k))
            if (isinstance(v, list)):
                # a list
                for x in v:
                    print('  {}'.format(x))
            elif (isinstance(v, dict)):
                # a dictionary
                for k1, v1 in v.items():
                    print('  {}'.format(k1))
                    print('    {}'.format(v1))
            else:
                # a value
                print('  {}'.format(v))


    def parse_EKmodel(self, args):
        '''
        set the sonar model to that provided in the command line

        Input:
            command line arguments
            parameter dictionary

        Output:
            revised parameter dictionary
        '''
        if (args.EKmodel):
            self.pars_dict['sonar_model'] = args.EKmodel
        else:
            print('No EK model provided! Try the -h option')
            exit()
        #return(pars)


    def parse_nc(self, args):
        '''
        set the output netCDF4 directory
        the default output directory for netCDF4 files is netCDF4_Files and
          is located as a subdirectory of the .raw data files directory

        Input:
            command line arguments
            parameter dictionary

        Output:
            revised parameter dictionary
        '''
        default_nc_dirname = 'netCDF4_Files'
        if (args.ncdirname):
            self.pars_dict['nc_dirname'] = args.ncdirname
        else:
            self.pars_dict['nc_dirname'] = default_nc_dirname
        #return(pars)


    def parse_filenames(self, args):
        '''
        populate the data file names and directories parameters
        the raw files can come from different directories. make a dictionary with
          netCDF4 output directory as the key and a list of the raw files
        CASES:
        file names are provided without specifying a data directory:
          file names must have the full path
          the output netCDF4 directory follows from the paths of the file names,
            where there can be different output directories
        data directory is specified with no file names:
          all .raw files are selected from the directory
          the output netCD4 directory follows from the data directory
        data directory and file names are provided:
          the specified files are selected and the netCD4 output directory follows
            from the data directory

        Input:
            command line arguments
            parameter dictionary

        Output:
            revised parameter dictionary
        '''
        #individual filenames were provided with no separate data directory
        if (args.filenames and not args.dataDirectory):
            print('filenames without data directory')
            for f in args.filenames:
                dataDirectory = f.parent
                outdir = dataDirectory / pars['nc_dirname']
                if not createOutDir(outdir):
                    exit()
                self.pars_dict.setdefault('EK_files', []).append(f)
        # only a data directory was provided
        if (args.dataDirectory and not args.filenames):
            print('data directory with no filenames was provided')
            outdir = args.dataDirectory / self.pars_dict['nc_dirname']
            if not createOutDir(outdir):
                exit()
            for f in args.dataDirectory.glob('**/*.raw'):
                #print('.raw file: ', f)
                self.pars_dict.setdefault('EK_files', []).append(args.dataDirectory / f)
        # data directory and filenames were provided
        if (args.dataDirectory and args.filenames):
            print('data directory with filenames were provided')
            outdir = args.dataDirectory / self.pars_dict['nc_dirname']
            if not createOutDir(outdir):
                exit()
            for f in args.filenames:
                self.pars_dict.setdefault('EK_files', []).append(args.dataDirectory / f)
        
        #return(pars)

    def parse_json(self, args):
        '''
        parse the json file
        overwrite files and paths in the par dictionary

        Input:
            command line arguments
            parameter dictionary

        Output:
            revised parameter dictionary
        '''

        print('json file provided')
        with open (args.jsonfile) as jsonfile:
            json_dict = json.load(jsonfile)

        # check the json EKmodel
        pars = parse_json_EKmodel(self, args, json_dict)

        # get the json directory paths
        pars = parse_json_paths(self, args, json_dict)

        # get the json file names
        pars = parse_json_filenames(self, args, json_dict)

        # get the metadata
        pars = parse_json_metadata(self, args, json_dict)

        #return(pars)

    def parse_json_EKmodel(self, args, json_dict):
        '''
        confirm that the sonar model provided in the command line is the same as
          that in the json file. If not, set the sonar model to the JSON file
          value and ask the user if they want to continue

        Input:
            command line arguments
            parameter dictionary
            json dictionary

        Output:
            revised parameter dictionary
        '''
        if (self.pars_dict['sonar_model'] != json_dict['sonar_model']):
            print('The command line sonar model: {0}, does not match the JSON ' \
                'sonar model: {1}!'.format(self.pars_dict['sonar_model'], json_dict['sonar_model']))
            print('The JSON sonar model: {} will be used'.format(json_dict['sonar_model']))
            answ = input('Do you want to continue [y/n]? ')
            if (answ == 'y'):
                self.pars_dict['sonar_model'] = json_dict['sonar_model']
            else:
                exit()
        #return(pars)

    def parse_json_paths(self, args, json_dict):
        '''
        get the paths to the data directories

        Input:
            command line arguments
            parameter dictionary
            json dictionary

        Output:
            revised parameter dictionary
        '''
        if (json_dict['path_config']):
            if (json_dict['path_config']['nc_dirname']):
                # netCDF4 output directory name provided
                self.pars_dict['nc_dirname'] = json_dict['path_config']['nc_dirname']
            # netCDF4 directory provided
            if (json_dict['path_config']['nc_data_path']):
                self.pars_dict['nc_data_path'] = Path(json_dict['path_config']['nc_data_path'])
                #if not createOutDir(ncdir):
                #    exit()
            if (json_dict['path_config']['EK_data_path'] and not
                json_dict['path_config']['nc_data_path']):
                    # data path provided but netCDF4 file path not provided
                    self.pars_dict['nc_data_path'] = Path(json_dict['path_config']['EK_data_path'])
            if not (json_dict['path_config']['EK_filenames']):
                # no way to figure out the output directory
                exit()
                # else will get output directory(s) from the file names
        else:
            print('File configurations not provided. No way to find data')
            exit()

            return(pars)


    def parse_json_filenames(self, args, json_dict):
        '''
        Get the file names
        Input:
            command line arguments
            parameter dictionary
            json dictionary
        Output:
            revised parameter dictionary
        '''
        # individual filenames were provided with no data directory
        if (json_dict['path_config']['EK_filenames'] and not
            json_dict['path_config']['EK_data_path']):
            print('filenames without data directory')
            for f in json_dict['path_config']['EK_filenames']:
                dataDirectory = f.parent
                outdir = dataDirectory / self.pars_dict['nc_dirname']
                if not createOutDir(outdir):
                    exit()
                self.pars_dict.setdefault('EK_files', []).append(f)
        # only a data directory was provided
        if (json_dict['path_config']['EK_data_path'] and not
            json_dict['path_config']['EK_filenames']):
            print('data directory with no filenames was provided')
            outdir = json_dict['path_config']['EK_data_path'] / self.pars_dict['nc_dirname']
            if not createOutDir(outdir):
                exit()
            for f in args.dataDirectory.glob('**/*.raw'):
                #print('.raw file: ', f)
                self.pars_dict.setdefault('EK_files', []).append(args.dataDirectory / f)
        # data directory and filenames were provided
        if (args.dataDirectory and args.filenames):
            print('data directory with filenames were provided')
            outdir = args.dataDirectory / self.pars_dict['nc_dirname']
            if not createOutDir(outdir):
                exit()
            for f in args.filenames:
                self.pars_dict.setdefault('EK_files', []).append(args.dataDirectory / f)

            if json_dict['path_config']['EK_data_filenames']:
                for f in json_dict['path_config']['EK_data_filenames']:
                    self.pars_dict.setdefault('EK_files', []). \
                            append(Path(json_dict['path_config']['EK_data_path']) / Path(f))
            #if json_dict['path_config']['EK_data_path']:
        else:
            print('No Data directory or files were provided in the json file!')
            print('Data directory and files should be provided in the arguments')

        #return(pars)


    def parse_json_metadata(self, args, json_dict):
        '''
        get and enter metadata for the ship
        Input:
            command line arguments
            parameter dictionary
            json dictionary
        Output:
            updated parameter dictionary
        '''
        if ('json_dict' in locals()):
            if (json_dict['platform']):
                pars.setdefault('platform', {}).update({'name' :
                    json_dict['platform']['name']})
                pars.setdefault('platform', {}).update({'type' :
                    json_dict['platform']['type']})
                pars.setdefault('platform', {}).update({'ICES_code' :
                    json_dict['platform']['ICES_code']})
        else:
            if (args.Pname):
                pars.setdefault('platform', {}).update({'name' : args.Pname})
            else:
                pars.setdefault('platform', {}).update({'name' : 'NA'})
            if (args.Ptype):
                pars.setdefault('platform', {}).update({'type' : args.Ptype})
            else:
                pars.setdefault('platform', {}).update({'type' : 'NA'})
            if (args.Pcode):
                pars.setdefault('platform', {}).update({'ICES_code' : args.Pcode})
            else:
                pars.setdefault('platform', {}).update({'ICES_code' : 'NA'})

        return(pars)


class file_management():
    def createOutDir(outputdir):
        '''
        Create an ouput directory for the netCDF4 files

        Input:
            output directory name with full path
            This should be a pathlib object. If not convert to one
            
        Output:
            True/False: True if the directory was created or already existed
                        False if the directory was not able to be created
        '''
        # check that the output directory name is a pathlib object
        if not isinstance(outputdir, Path):
            outputdir = Path(outputdir)

        # create the output directory
        success = True
        if (outputdir.exists()):
            print('Directory {0} exists'.format(outputdir))
            success = True
        else:
            try:
                outputdir.mkdir()
                success = True
            except OSError:
                print('Unable to create output directory {0}'.format(outputdir))
                success = False
                #exit()
            else:
                print('Output directory created {0}'.format(outputdir))
                success = True
        return(success)


