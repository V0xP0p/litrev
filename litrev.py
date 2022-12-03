import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import datetime


class LitRev:

    def __init__(self,
                 df,
                 year_start,
                 year_end=datetime.date.today().year,
                 drop_values=None,
                 top_count=20,
                 top_citations=5):
        # initialize the literature table and remove unneeded columns
        self.input = df.loc[:, ['Document Title', 'Authors', 'Abstract','Author Keywords', 'IEEE Terms',
                                'Article Citation Count', 'Publication Year', 'DOI']]
        # find unique terms in the literature
        self.terms = pd.unique(pd.concat([df["Author Keywords"].str.split(";", expand=True).stack(),
                                          self.input["IEEE Terms"].str.split(";", expand=True).stack()]))
        self.drop_vals = drop_values
        # Split list terms, merge and expand the dataframe
        self.lit = self.term_split(self.input, self.drop_vals)
        self.year_start = year_start
        self.year_end = year_end
        self.top_count = top_count
        self.top_citations = top_citations
        self.counts = self.get_counts()
        self.top_counts = self.get_top()


    @staticmethod
    def term_split(df,
                   drop_values):

        df_final = df.assign(var1=df["Author Keywords"].str.split(';'), var2=df["IEEE Terms"].str.split(';'))

        df_final['var1'] = df_final['var1'].apply(lambda d: d if isinstance(d, list) else [])
        df_final['var2'] = df_final['var2'].apply(lambda d: d if isinstance(d, list) else [])
        df_final['Terms'] = df_final['var1'] + df_final['var2']

        df_final = df_final.drop(['var1', 'var2', 'Author Keywords', 'IEEE Terms'], axis=1)
        df_final['Terms'] = df_final['Terms'].map(lambda x: list(map(lambda y: y.lower(), x)), na_action='ignore')
        df_final['Terms'] = df_final['Terms'].map(lambda x: list(set(x)), na_action='ignore')
        # remove values matching drop list
        # if drop_values:
        df_final = df_final.explode('Terms')
        df_final['Terms'] = df_final['Terms'].fillna('None')
        if drop_values:
            df_final = df_final[~df_final.Terms.str.contains('|'.join(drop_values))]

        return df_final

    def get_counts(self):

        list_terms = []
        list_counts = []
        list_year = []

        for year in sorted(list(self.lit[(self.lit['Publication Year'] >= self.year_start) &
                                (self.lit['Publication Year'] <= self.year_end)]['Publication Year'].unique())):
            list_terms.extend(self.lit[self.lit['Publication Year'] == year].Terms.value_counts()[:self.top_count].index.tolist())
            list_counts.extend(self.lit[self.lit['Publication Year'] == year].Terms.value_counts()[:self.top_count].values)
            list_year.extend([year for x in range(self.top_count)])

        df_counts = pd.DataFrame({'Year': list_year, 'Terms': list_terms, 'Count': list_counts})

        citations = []
        for entry in range(len(df_counts.index)):
            citations.append(self.lit[(self.lit['Publication Year'] == df_counts.loc[entry, 'Year']) &
                                      (self.lit['Terms'] == df_counts.loc[entry, 'Terms'])]
                             ['Article Citation Count'].sum())
        df_counts['Citations'] = citations

        return df_counts

    def get_top(self):

        reduced_terms = self.counts.Terms.value_counts()[:self.top_count].index.tolist()
        reduced_count = []
        reduced_citations = []
        for reduced_term in reduced_terms:
            reduced_count.append(self.counts[self.counts['Terms'] == reduced_term]['Count'].sum())
            reduced_citations.append(self.counts[self.counts['Terms'] == reduced_term]['Citations'].sum())

        return pd.DataFrame({'Term': reduced_terms, 'Count': reduced_count, 'Citations': reduced_citations})

    def plot_common_terms(self,
                          style="white",
                          sizes=(40, 400),
                          alpha=.5,
                          palette="muted",
                          height=8,
                          title="Most Common Keywords in Submitted Papers",
                          xlabel="Number of papers",
                          ylabel="Keywords"):

        sns.set_theme(style=style)

        # Plot miles per gallon against horsepower with other semantics
        sns.relplot(x="Count", y="Term", size="Citations",
                    sizes=sizes, alpha=alpha, palette=palette,
                    height=height, data=self.top_counts)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

    def plot_most_cited(self,
                        style='white',
                        kind='kde',
                        height=6,
                        multiple='fill',
                        clip=(0, None),
                        palette="ch:rot=-.25,hue=1,light=.75",
                        title='Distribution of Citations for most cited terms',
                        xlabel='Year',
                        ylabel='Citation Density',
                        ):

        sns.set_theme(style="white")
        df_most_cited = self.counts[self.counts['Terms'].isin(
            self.top_counts.sort_values(by='Citations', ascending=False)['Term'][:self.top_citations])]
        sns.displot(
            data=df_most_cited,
            x='Year', hue='Terms',
            kind=kind, height=height,
            multiple=multiple, clip=clip,
            palette=palette
        )

        plt.xlim(self.year_start, self.year_end)
        plt.xlabel(xlabel)
        plt.xticks([year for year in range(self.year_start, self.year_end)])
        plt.ylabel(ylabel)
        plt.title(title)


if __name__ == "__main__":
    df = pd.read_csv("export2022.12.02-16.15.50.csv")
    covid_lit = LitRev(df, year_start=2020)

