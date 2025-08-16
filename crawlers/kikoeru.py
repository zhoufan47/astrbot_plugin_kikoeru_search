from typing import Dict, Any

ITEM_NOT_FOUND = "不存在"


def parse_result(response)-> Dict[str, Any]:
    title = response.get("title", ITEM_NOT_FOUND)  # 作品名称
    pid = "RJ" + str(response.get("id", 0))  # 作品ID
    price = response.get("price", 0)  # 售价
    sales = response.get("dl_count", 0)  # 销量
    nsfw = response.get("nsfw", False)  # 年龄分级
    main_cover_url = response.get("mainCoverUrl")
    age_limit = "R-18" if nsfw else "全年龄"
    rating = response.get("rating", 0)  # 评分
    rating_count = response.get("rating_count", 0)  # 评价人数
    release_date = response.get("release", "未知")
    # 制作团队
    makers = response.get("name", None)
    if makers is None:
        makers = response.get("circle", {}).get("name", "未知")
    # 表演者
    artists_source = response.get("vas", [])
    artists = ",".join([artist.get("name", "") for artist in artists_source])
    # 插画师
    illustrators_source = response.get("illustrators", [])
    illustrators = ",".join([illustrator.get("name", "") for illustrator in illustrators_source])

    # tags
    genres_source = response.get("tags", [])
    genres = ",".join([genre.get("name", "") for genre in genres_source])

    result_dict = {
        "title": title,
        "pid": pid,
        "price": price,
        "sales": sales,
        "rate_grade": age_limit,
        "rating": rating,
        "rating_count": rating_count,
        "tags": genres,
        "illustrators": illustrators,
        "artists": artists,
        "release_date": release_date,
        "main_cover_url": main_cover_url,
        "makers":makers
    }
    return result_dict