from scipy.stats import combine_pvalues
import statsmodels.stats.multitest as smt
import pandas as pd

def aggregate(pvals, method):

    pvals = pd.Series(pvals)

    if method == 'fisher':
        return combine_pvalues(pvals, method='fisher', weights = None)[1]
        
    elif method == 'sidak':
        return min(smt.multipletests(pvals, method = 'sidak')[1])

    elif method == 'simes':
        return simes(pvals)

    elif method == 'fdr':
        return min(smt.multipletests(pvals, method = 'fdr_bh')[1])

    return
    
def simes(p_vals):
    # For a gene containing n p-value, the combined P-value is defined as
    # p{s}=min{np{r}/r;r=1,2…,n} where the p{r} are the individual nucleotide P-values sorted
    # in increasing order. This provides weak control of the family-wise error rate
    # across the set of null hypotheses for all nucleotides in the gene. 
    sorted = p_vals.sort_values()
    ranks = pd.Series(range(1, len(p_vals) + 1))
    multiplied = sorted * len(ranks)
    results = multiplied/ranks.values
    return min(results)
