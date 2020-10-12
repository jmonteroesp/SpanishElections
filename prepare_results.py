# objetivo: obtener tabla de votos y de escaños
# para hacer una prueba más tarde

import pandas as pd
import string
import os.path
import pdb



def save_df_to_pkl(df, save_dir, filename):
    df.to_pickle(os.path.join(save_dir, filename))


def clean_string_columns(df, columns_to_strip):
    '''
    Parameters
    - df: pandas.DataFrame that must at least contain a column named Province
    with province names as given in the original excel file.
    - columns_to_strip: list of columns to be stripped from blank spaces
    Returns
    - df with Province and other string columns cleaned
    '''
    # simplify name of main columns
    df.columns = df.columns.str.replace("nombre de ", "")
    # strip columns with blank spaces
    for col in columns_to_strip:
        df[col] = df[col].str.strip()
    # remove alternative names of Provincias (defined after a /)
    df.provincia = df.provincia.str.replace(r" / .*$", "")
    return df


def extract_general_data(lookup_table, save_output=False,
                         save_dir=None, filename='general_data.pkl'):
    '''
    Arguments:
    - lookup_table is a pandas dataframe from reading the excel with the results
    of general elections published by Spanish official authorities
    - save_output, boolean whether to save the output
    - save_dir, directory where to save the output. only active if save_output is
    True

    Return:
    - general_data: a pandas dataframe with general information of the elections
    by province. Columns:
    ['comunidad', 'código de provincia', 'provincia', 'población',
       'número de mesas', 'censo electoral sin cera', 'censo cera',
       'total censo electoral', 'solicitudes voto cera aceptadas',
       'total votantes cer', 'total votantes cera', 'total votantes',
       'votos válidos', 'votos a candidaturas', 'votos en blanco',
       'votos nulos', 'diputados']
    '''
    # p is the last column with general data (check excel)
    last_column_index = string.ascii_lowercase.index('q')
    general_data = lookup_table.iloc[:, :last_column_index]
    # drop column levels 0 and 1
    general_data = general_data.droplevel(0, axis=1)
    # pass all column names to lower case
    general_data.columns = general_data.columns.str.lower()
    # clean province and autonomous community columns
    general_data = \
    clean_string_columns(general_data,
                         columns_to_strip=['comunidad', 'provincia'])
    # cast province code to integer
    general_data['código de provincia'] = \
    general_data['código de provincia'].astype('int8')

    # add diputados per province
    indices_with_diputados = [idx for idx, col in enumerate(lookup_table.columns)
                              if col[1] == 'Diputados']
    general_data['diputados'] = lookup_table.iloc[:, indices_with_diputados]\
                                .sum(axis=1)
    if save_output:
        save_df_to_pkl(general_data, save_dir, filename)
    return general_data


def extract_results_by_province(lookup_table, save_output=False,
                                save_dir=None, filename='results_by_province.pkl'):
    '''
    Arguments:
    - lookup_table is a pandas dataframe from reading the excel with the results
    of general elections published by Spanish official authorities
    - save_output, boolean whether to save the output
    - save_dir, directory where to save the output. only active if save_output is
    True

    Return:
    - results: a pandas dataframe with the results by province and political party
    in terms of votes and seats
    '''
    first_column_index = string.ascii_lowercase.index('q')
    # select columns with results from excel
    # column 2 is Province name
    # results come from first_column_index on
    column_indices_to_select = \
    [2] + list(range(first_column_index, lookup_table.shape[1]))
    results = lookup_table.iloc[:, column_indices_to_select]
    # pass to long format
    province_column_name = results.columns[0]
    results = results.melt(id_vars=[province_column_name],
                           var_name=['party', 'result'])
    # set results.result values to lowercase
    results.result = results.result.str.lower()
    # rename Provincia column
    results.columns = ['provincia'] + list(results.columns[1:])
    # clean string columns
    results = clean_string_columns(results, ['provincia'])
    if save_output:
        save_df_to_pkl(results, save_dir, filename)
    return results


if __name__ == '__main__':
    input_dir = 'data/input/'
    output_dir = 'data/output/'
    lookup = pd.read_excel(input_dir + "PROV_02_201911_1.xlsx",
                       header=[4, 5], nrows=52)
    results = extract_results_by_province(lookup, save_output=True,
                                          save_dir=output_dir)
    general_data = extract_general_data(lookup, save_output=True,
                                        save_dir=output_dir)
    pdb.set_trace()


run_old = False
if run_old:
    # general data, that will be appended to both datasets
    first_row_cols = df.columns.get_level_values(0)
    # function to find last column with unnamed
    def find_unnamed(list):
        index_last_unnamed = -1
        for item in list:
            if item.startswith("Unnamed"):
                index_last_unnamed += 1
            else:
                return index_last_unnamed
    index_general = find_unnamed(first_row_cols)

    df_general = df.iloc[:, :(index_general+1)]
    df_general.columns = df_general.columns.droplevel([0, 1])

    # simplify name of main columns
    df_general.columns = df_general.columns.str.replace("Nombre de ", "")
    # note need to trim strings (Comunidad, Provincia)
    df_obj = df_general.select_dtypes(['object'])
    df_general[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
    # remove alternative names of Provincia column (defined after a /)
    df_general.Provincia = df_general.Provincia.str.replace(r" / .*$", "")
    # pdb.set_trace()
    # convert Codigo de Provincia to number
    df_general['Código de Provincia'] = df_general['Código de Provincia'].astype('int32')

    # notice use of xs to just restrict by third level
    df_votos = df.xs('Votos', axis=1, level=2, drop_level=False)
    df_votos.columns = df_votos.columns.droplevel([0, 2])
    df_votos = pd.concat([df_general['Provincia'],
                          df_votos], axis=1)

    # chequeo de concat: suman todos los votos los votos a candidaturas?
    df_suma = df_votos.sum(axis=1)
    # pdb.set_trace()
    if all(df_general['Votos a candidaturas'] == df_suma):
        print('Suma de votos en df_votos igual a votos totales a candidaturas')

    # do the same with seats
    df_diputados = df.xs('Diputados', axis=1, level=2, drop_level=True)
    df_diputados.columns = df_diputados.columns.droplevel(0)
    df_diputados = pd.concat([df_general['Provincia'], df_diputados], axis=1)

    # need to add seats to divide
    seats = df_diputados.sum(axis=1)
    df_votos = pd.concat([df_votos, seats], axis=1)
    df_votos.rename(columns={0:'Diputados'}, inplace=True)

    # order df_votos columns
    #pdb.set_trace()
    cols_df_votos = list(df_votos.columns)
    cols_df_votos = [cols_df_votos[0]] + [cols_df_votos[-1]] + cols_df_votos[1:-1]
    df_votos = df_votos[cols_df_votos]

    # save dataframes
    # df_general.to_pickle("./resultados.pkl")
    # df_votos.to_pickle('./votos.pkl')
    # df_diputados.to_pickle('./diputados.pkl')

    pdb.set_trace()
