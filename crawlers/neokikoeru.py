from typing import Dict, Any

# 评级数据
RATE_GRADE = {
    0: "不存在",
    1: "全年龄",
    2: "R-15",
    3: "R-18"
}
ITEM_NOT_FOUND = "不存在"


def parse_result(response)-> Dict[str, Any]:
    pid = response.get("id", ITEM_NOT_FOUND)  # 作品ID
    name = response.get("name", ITEM_NOT_FOUND)  # 作品名称
    price = response.get("price", 0)  # 售价
    sales = response.get("sales", 0)  # 销量
    age_category = response.get("age_category", 0)  # 年龄分级
    grade_cn = RATE_GRADE.get(age_category, "未知")
    rating = response.get("rating", 0)  # 评分
    rating_count = response.get("rating_count", 0)  # 评价人数
    release_date = response.get("release_date", "未知")
    makers = response.get("maker", {}).get("name", "未知")
    # 表演者
    artists_source = response.get("artists", [])
    artists = ",".join([artist.get("name", "") for artist in artists_source])
    # 插画师
    illustrators_source = response.get("illustrators", [])
    illustrators = ",".join([illustrator.get("name", "") for illustrator in illustrators_source])
    # tags
    genres_source = response.get("genres", [])
    genres = ",".join([genre.get("name", "") for genre in genres_source])
    main_cover_url = response.get("image_main")
    result_dic = {
        "title": name,
        "pid": pid,
        "price": price,
        "sales": sales,
        "rate_grade": grade_cn,
        "rating": rating,
        "rating_count": rating_count,
        "tags": genres,
        "illustrators": illustrators,
        "artists": artists,
        "release_date": release_date,
        "main_cover_url": main_cover_url,
        "makers":makers
    }
    return result_dic