import pandas as pd

def make_rating_df():
    movies_df = pd.read_csv("./ml-32m/movies.csv")
    ratings_df = pd.read_csv("./ml-32m/ratings.csv")
    tags_df = pd.read_csv("./ml-32m/tags.csv")

    ratings_df = ratings_df.drop(columns=['userId'])

    rate_movies = ratings_df.groupby('movieId')['rating'].mean().reset_index()
    rate_movies.columns = ['movieId', 'mean_rating']
    rate_movies = pd.merge(rate_movies, movies_df, on='movieId', how='inner')

def get_top_n_by_genres(df, genres, n=10):
    """
    Возвращает топ-N фильмов по среднему рейтингу, содержащих все жанры из списка.
    
    :param df: DataFrame с колонками ['movieId', 'mean_rating', 'title', 'genres']
    :param genres: Список жанров, например ['Comedy', 'Drama']
    :param n: Количество фильмов в топе
    :return: DataFrame с топ-N фильмами
    """
    # Фильтрация: фильм должен содержать все жанры
    filtered_df = df.copy()
    for genre in genres:
        filtered_df = filtered_df[filtered_df['genres'].str.contains(genre, case=False, na=False)]
    
    # Сортировка по рейтингу
    top_n = filtered_df.sort_values(by='mean_rating', ascending=False).head(n)
    
    return top_n[['title', 'mean_rating', 'genres']]
