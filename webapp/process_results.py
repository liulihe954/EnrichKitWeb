import pandas as pd

def process_results(input_list):
    #
    did_cut = False
    if len(input_list) > 201:
            num_to_cut = 200
            did_cut = True
    else:
        num_to_cut = len(input_list)
    #
    header = input_list[0]
    if input_list[0][0] == 'Term ID':
        tmp_df = pd.DataFrame(input_list[1:])
        tmp_df_sort = tmp_df.sort_values(tmp_df.columns[-1])
        tmp_df_filter = tmp_df_sort[tmp_df_sort[tmp_df.columns[1]] != 'msigdb']   
        df_to_cut_list = tmp_df_filter.head(num_to_cut).values.tolist()
    else:
        df_to_cut_list = input_list[1:201]

    return header, df_to_cut_list, did_cut

    

