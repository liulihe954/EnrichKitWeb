import pandas as pd

def process_results(input_list):
    #
    did_cut = False
    trunked_list = []
    header = input_list[0]
    for item in input_list[1:]:
        if (len(item) <=7 or len(item) in [8,10,12]) and len(trunked_list) < 200:
            trunked_list.append(item)
    #
    df_to_cut_list = trunked_list
    # if input_list[0][0] == 'Term ID':
    #     tmp_df = pd.DataFrame(input_list[1:])
    #     tmp_df_sort = tmp_df.sort_values(tmp_df.columns[-1])
    #     tmp_df_filter = tmp_df_sort[tmp_df_sort[tmp_df.columns[1]] != 'msigdb']   
    #     df_to_cut_list = tmp_df_filter.head(num_to_cut).values.tolist()
    #     df_to_cut_list = df_to_cut_list[1:201]
    # else:
    #     df_to_cut_list = trunked_list # input_list[1:201]

    return header, df_to_cut_list, did_cut

    

