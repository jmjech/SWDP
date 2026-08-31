# -*- coding: utf-8 -*-
"""
convert_EK-to-netCDF4 

Use echopype to convert Simrad EK60 and EK80 raw files to netCDF4 format

jech
"""

import echopype as ep
from echopype import open_raw
from pathlib import Path, PurePath
import json
from sys import exit
import sys
import argparse
#import utils

def create_outdir(outputdir):
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


def parse_args(args, showit=True):
    '''
    Parse the argument list and return a dictionary with the file names and paths

    Input:
        command line arguments as argparse object
        optional - showit
            True will display/print-to-screen the resulting dictionary
            False will not display/print-to-screen the resulting dictionary

    Output:
        dictionary with output file directories as the keys and filenames
        as the values
    '''
    pars_dict = {}

    # set the sonar model to that provided in the command line
    pars_dict['sonar_model'] = args.EKmodel

    # the default output directory for netCDF4 files is netCDF4_Files and
    # is located in as a subdirectory of the .raw data files directory
    default_nc_dirname = 'netCDF4_Files'
    if (args.ncdirname):
        pars_dict['nc_dirname'] = args.ncdirname
    else:
        pars_dict['nc_dirname'] = default_nc_dirname

    ###
    # parse the file names and paths from the arguments
    # the raw files can come from different directories, so make a dictionary with 
    # netCDF4 output directory as the key and a list of the raw files 
    # individual filenames were provided with no separate data directory
    if (args.filenames and not args.dataDirectory):
        print('filenames without data directory')
        for f in args.filenames:
            dataDirectory = f.parent
            outdir = dataDirectory / pars_dict['nc_dirname']
            if not create_outdir(outdir):
                exit()
            pars_dict.setdefault('EK_files', []).append(f)
    # only a data directory was provided
    if (args.dataDirectory and not args.filenames):
        print('data directory with no filenames was provided')
        outdir = args.dataDirectory / pars_dict['nc_dirname']
        if not create_outdir(outdir):
            exit()
        for f in args.dataDirectory.glob('**/*.raw'):
            #print('.raw file: ', f)
            pars_dict.setdefault('EK_files', []).append(args.dataDirectory / f)
    # data directory and filenames were provided
    if (args.dataDirectory and args.filenames):
        print('data directory with filenames were provided')
        outdir = args.dataDirectory / pars_dict['nc_dirname']
        if not create_outdir(outdir):
            exit()
        for f in args.filenames:
            pars_dict.setdefault('EK_files', []).append(args.dataDirectory / f)

    if (args.jsonfile):
        # json file provided - overwrites files and paths if they were provided in
        # the command line
        print('json file provided')
        with open (args.jsonfile) as jsonfile:
            json_dict = json.load(jsonfile)
        
        # confirm that the sonar model provided in the command line is the same as
        # that in the json file. If not, set the sonar model to the JSON file
        # value and ask the user if they want to continue
        if (pars_dict['sonar_model'] != json_dict['sonar_model']):
            print('The command line sonar model: {0}, does not match the JSON ' \
                'sonar model: {1}!'.format(pars_dict['sonar_model'], json_dict['sonar_model']))
            print('The JSON sonar model: {} will be used'.format(json_dict['sonar_model']))
            answ = input('Do you want to continue [y/n]? ')
            if (answ == 'y'):
                pars_dict['sonar_model'] = json_dict['sonar_model']
            else:
                exit()

        if (json_dict['path_config']):
            if (json_dict['path_config']['nc_dirname']):
                # netCDF4 output directory name provided
                pars_dict['nc_dirname'] = json_dict['path_config']['nc_dirname']
            # netCDF4 file path provided
            if (json_dict['path_config']['nc_data_path']):
                ncdir = Path(json_dict['path_config']['nc_data_path'])
                pars_dict['nc_dirname'] = ncdir
                if not create_outdir(ncdir):
                    exit()
            if (json_dict['path_config']['EK_data_path'] and not
                json_dict['path_config']['nc_data_path']):
                    # data path provided but netCDF4 file path not provided
                    ncdir = Path(json_dict['path_config']['EK_data_path']) / default_nc_dir 
                    pars_dict['nc_dirname'] = ncdir
            if not (json_dict['path_config']['EK_filenames']):
                # no way to figure out the output directory
                exit()
                # else will get output directory(s) from the file names

            # individual filenames were provided with no data directory
            if (json_dict['path_config']['EK_filenames'] and not 
                json_dict['path_config']['EK_data_path']):
                print('filenames without data directory')
                for f in json_dict['path_config']['EK_filenames']:
                    dataDirectory = f.parent
                    outdir = dataDirectory / pars_dict['nc_dirname']
                    if not create_outdir(outdir):
                        exit()
                    pars_dict.setdefault('EK_files', []).append(f)
            # only a data directory was provided
            if (json_dict['path_config']['EK_data_path'] and not 
                json_dict['path_config']['EK_filenames']):
                print('data directory with no filenames was provided')
                outdir = json_dict['path_config']['EK_data_path'] / pars_dict['nc_dirname']
                if not create_outdir(outdir):
                    exit()
                for f in args.dataDirectory.glob('**/*.raw'):
                    #print('.raw file: ', f)
                    pars_dict.setdefault('EK_files', []).append(args.dataDirectory / f)
            # data directory and filenames were provided
            if (args.dataDirectory and args.filenames):
                print('data directory with filenames were provided')
                outdir = args.dataDirectory / pars_dict['nc_dirname']
                if not create_outdir(outdir):
                    exit()
                for f in args.filenames:
                    pars_dict.setdefault('EK_files', []).append(args.dataDirectory / f)

                if json_dict['path_config']['EK_data_filenames']:
                    for f in json_dict['path_config']['EK_data_filenames']:
                        pars_dict.setdefault('EK_files', []). \
                                append(Path(json_dict['path_config']['EK_data_path']) / Path(f))
                #if json_dict['path_config']['EK_data_path']:
        else:
            print('No Data directory or files were provided in the json file!')
            print('Data directory and files should be provided in the arguments')

    # get the platform codes for the metadata
    if ('json_dict' in locals()):
        if (json_dict['platform']):
            pars_dict.setdefault('platform', {}).update({'name' :
                json_dict['platform']['name']})
            pars_dict.setdefault('platform', {}).update({'type' : 
                json_dict['platform']['type']})
            pars_dict.setdefault('platform', {}).update({'ICES_code' : 
                json_dict['platform']['ICES_code']})
    else:
        if (args.Pname):
            pars_dict.setdefault('platform', {}).update({'name' : args.Pname})
        else:
            pars_dict.setdefault('platform', {}).update({'name' : 'NA'})
        if (args.Ptype):
            pars_dict.setdefault('platform', {}).update({'type' : args.Ptype})
        else:
            pars_dict.setdefault('platform', {}).update({'type' : 'NA'})
        if (args.Pcode):
            pars_dict.setdefault('platform', {}).update({'ICES_code' : args.Pcode})
        else:
            pars_dict.setdefault('platform', {}).update({'ICES_code' : 'NA'})

    if (showit):
        for k, v in pars_dict.items():
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

    return(pars_dict)
    # test for pathlib object
    #if (isinstance(k, PurePath)):

    
def main(args):
    # parse the arguments and get the filenames and paths
    pars_dict = utils.parse_args(args, showit=True)
    print(pars_dict['sonar_model'])

    # convert each to netCDF4    
    for f in pars_dict['EK_files']:
        print('Converting: ', f)
        ed = open_raw(str(f), sonar_model=pars_dict['sonar_model'])
        # Henry B. Bigelow ICES code is 33HH
        ed['Platform']['platform_name'] = pars_dict['platform']['name']
        ed['Platform']['platform_type'] = pars_dict['platform']['type']
        ed['Platform']['platform_code_ICES'] = pars_dict['platform']['ICES_code']
        # the to_netcdf function seems to have an error catch, so I don't use "try"
#        ed.to_netcdf(save_path=str(f.parent / pars_dict['nc_dirname']))
    

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Convert EK .raw files to \
        Echopype netCDF4 format')
    parser.add_argument('EKmodel', nargs='?', choices=['EK60', 'EK80'], 
            help='mandatory argument!')
    parser.add_argument('-dd', '--dataDirectory', type=Path, help='data file \
        directory')
    parser.add_argument('-f', '--filenames', type=Path, default=[], nargs='+',
            help='data file name(s) with full path if no data directory is \
            provided: returns a list')
    parser.add_argument('-j', '--jsonfile', type=Path, help='json file full \
        path and file name')
    parser.add_argument('-pn', '--Pname', help='Platform code: name')
    parser.add_argument('-pt', '--Ptype', help='Platform code: type')
    parser.add_argument('-pc', '--Pcode', help='Platform code: ICES code')
    parser.add_argument('-nc', '--ncdirname', type=Path, help='netCDF4 output \
            directory name')
    args = parser.parse_args()

    if (args.EKmodel is None):
        print('Mandatory Argument EKmodel is not Provided! Try the -h option')
        exit()
    elif (args.dataDirectory is None and len(args.filenames) == 0 and args.jsonfile is None):
        print('No files Provided! Try the -h option')
        exit()
    else:
        main(args)

    #if any(vars(args).values()):
    #    main(args)
    #else:
    #    print('No Arguments Provided! Try the -h option')

