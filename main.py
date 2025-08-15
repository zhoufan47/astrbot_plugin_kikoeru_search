from typing import Any, Coroutine

import aiohttp
from astrbot.core.message.components import Image

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


@register("kikoeru_search", "棒棒糖", "查询ASMR库数据", "1.0.0")
class MyPlugin(Star):
    #评级数据
    RATE_GRADE = {
        0: "不存在",
        1: "全年龄",
        2: "R-15",
        3: "R-18"
    }
    def __init__(self, context: Context,config: dict):
        super().__init__(context)
        #用来访问本地库的http_session
        self.http_session_local = aiohttp.ClientSession(trust_env=False)
        #用来访问ASMR.ONE的http_session,使用astrbot提供的代理信息
        self.http_session_proxy = aiohttp.ClientSession(trust_env=True)
        self.config = config
        #本地库地址
        self.api_url = config.get('api_url')
        #本地库cookies
        self.api_key = config.get('api_key')
        #asmr.one 的 cookies
        self.remote_key = config.get('remote_key')
        #本地库的外部网络访问地址
        self.external_url = config.get('external_url')
        #查询远程ASMR库是是否检查本地库是否存在该作品
        self.check_local_flag = config.get('check_local_flag')
        logger.info("插件 [kikoeru_search] 已初始化。")

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("本地奥术")
    async def local_lib_search(self, event: AstrMessageEvent,query_str: str):
        logger.info(f"查询条件{query_str}")
        try:
            response = await self.query_local_repository("check", query_str)
            pid = response.get("id")                #作品ID
            if pid == 'donotexits':
                yield event.plain_result(f"本地资源库不存在作品{query_str},可以下载！")
                return

            name = response.get("name")             #作品名称
            price = response.get("price",0)          #售价
            sales = response.get("sales", 0)                #销量
            age_category = response.get("age_category",0) #年龄分级
            logger.info(f"年龄分级数据:{age_category}")
            grade_cn = self.RATE_GRADE.get(age_category)
            rating = response.get("rating",0)       #评分
            rating_count = response.get("rating_count", 0) #评价人数
            release_date = response.get("release_date", "未知")
            makers = response.get("maker").get("name")

            # 表演者
            artists_list = []
            artists_source = response.get("artists")
            # 使用 for 循环遍历这个列表
            for artist_dict in artists_source:
                # 在每次循环中，从当前的字典中提取 "name" 键的值
                artists_list.append(artist_dict["name"])
            artists = ",".join(artists_list)

            #插画师
            illustrators_list = []
            illustrators_source = response.get("illustrators")
            # 使用 for 循环遍历这个列表
            for illustrators_dict in illustrators_source:
                # 在每次循环中，从当前的字典中提取 "name" 键的值
                illustrators_list.append(illustrators_dict["name"])
            illustrators = ",".join(illustrators_list)

            #tags
            genres_list = []
            genres_source = response.get("genres")
            # 使用 for 循环遍历这个列表
            for genres_dict in genres_source:
                # 在每次循环中，从当前的字典中提取 "name" 键的值
                genres_list.append(genres_dict["name"])
            genres = ",".join(genres_list)
            reply_message = (
                f"✅ 查询成功！\n"
                f"--------------------\n"
                f"🎬 标题: {name}\n"
                f"🔢 番号: {pid}\n"
                f"📅 发行日:{release_date}\n"
                f"🏢 制作组:{makers}\n"
                f"🎤 演员:{artists}\n"
                f"🎨 插画师:{illustrators}\n"
                f"🏷️ 标签:{genres}\n"
                f"💸 售价:{price}\n"
                f"🏬 销量:{sales}\n"
                f"🌟 评分:{rating}\n"
                f"😃 评分人数:{rating_count}\n"
                f"⛔ 年龄分级:{grade_cn}\n"
                f"--------------------\n"
            )
            yield event.plain_result(reply_message)
        except aiohttp.ClientResponseError as e:
            logger.error(f"插件 [kikoeru_search] 请求API时服务器返回错误: {e.status} {e.message}")
            yield event.plain_result(f"请求失败，服务器返回错误码：{e.status}")
        except Exception as e:
            logger.error(f"插件 [kikoeru_search] 处理命令 时发生未知错误: {e}", exc_info=True)
            yield event.plain_result("插件处理时发生未知错误，请联系管理员查看后台日志。")
            return

    @filter.command("远程奥术")
    async def remote_lib_search(self, event: AstrMessageEvent,query_str: str):
        logger.info(f"查询条件: {query_str}")
        try:
            yield event.plain_result(f"开始查询远端资源库 {query_str} 的信息……")
            response = await self.query_remote_repository("check", query_str)
            pid = "RJ" + str(response.get("id"))  # 作品ID
            name = response.get("title")  # 作品名称
            price = response.get("price", 0)  # 售价
            sales = response.get("dl_count", 0)  # 销量
            nsfw = response.get("nsfw", False)  # 年龄分级
            main_cover_url = response.get("mainCoverUrl")
            if nsfw:age_limit="是"
            else:age_limit="否"
            rating = response.get("rating", 0)  # 评分
            rating_count = response.get("rating_count", 0)  # 评价人数
            release_date = response.get("release", "未知")
            # 制作团队
            makers = response.get("name", "未知")

            # 表演者
            artists_list = []
            for item in response.get("vas",[]):
                artists_list.append(item["name"])
            artists = ",".join(artists_list)

            # 插画师
            illustrators_list = []
            for item in response.get("illustrators",[]):
                illustrators_list.append(item["name"])
            illustrators = ",".join(illustrators_list)

            # tags
            genres_list = []
            for item in response.get("tags",[]):
                genres_list.append(item["name"])
            genres = ",".join(genres_list)
            reply_message = (
                f"✅ 查询成功！\n"
                f"--------------------\n"
                f"🎬 标题:{name}\n"
                f"🔢 番号:{pid}\n"
                f"📅 发行日:{release_date}\n"
                f"🏢 制作组:{makers}\n"
                f"🎤 演员:{artists}\n"
                f"🎨 插画师:{illustrators}\n"
                f"🏷️ 标签:{genres}\n"
                f"💸 售价:{price}\n"
                f"🏬 销量:{sales}\n"
                f"🌟 评分:{rating}\n"
                f"😃 评分人数:{rating_count}\n"
                f"⛔ 是否R-18:{age_limit}\n"
                f"--------------------\n"
            )
            yield event.plain_result(reply_message)
            logger.info("检测到封面，地址" + main_cover_url)
            headers = {
                "authorization": f"Bearer {self.remote_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            }

            img_response = await self.http_session_proxy.get(main_cover_url, headers=headers)
            img_response.raise_for_status()
            img_data = await img_response.read()
            chain = [
                Image.fromBytes(img_data)
            ]
            yield event.chain_result(chain)
            if self.check_local_flag:
                rsp = await self.query_local_repository("check", query_str)
                rst = rsp.get("id")
                if rst =='donotexits':
                    yield event.plain_result(f"本地资源库不存在作品{query_str},可以下载！")
                else:
                    yield event.plain_result(f"本地资源库已存在作品{query_str}")
        except aiohttp.ClientResponseError as e:
            logger.error(f"插件 [kikoeru_search] 请求API时服务器返回错误: {e.status} {e.message}")
            yield event.plain_result(f"请求失败，服务器返回错误码：{e.status}")
        except Exception as e:
            logger.error(f"插件 [kikoeru_search] 处理命令 时发生未知错误: {e}", exc_info=True)
            yield event.plain_result("插件处理时发生未知错误，请联系管理员查看后台日志。")
        return

    async def query_local_repository(self,trade_type:str,params:str) -> dict:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "authorization":f"Bearer {self.api_key}",
        }
        if trade_type == 'search':
            # 搜索场景
            url = self.api_url + "/api/v1/works"
            logger.info(f"搜索场景，条件 {params}")
        elif trade_type == 'check':
            #检查场景
            url = self.api_url + "/api/v1/work/" + params
            logger.info(f"检测场景，条件 {params}")
        else:
            url = self.api_url + "/api/v1/works" + params
            logger.info(f"未知场景，条件 {params}")

        async with self.http_session_local.get(url, params=params,headers=headers) as response:
            response.raise_for_status()
            logger.info(f"HTTP STATUS: {response.status}")
            if response.status == 404:
                return {id:"donotexits"}
            return await response.json()

    async def query_remote_repository(self,trade_type:str,params:str) -> dict:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "authorization":f"Bearer {self.remote_key}",
            "Referer":f"https://asmr.one/",
            "Sec-Ch-Ua":"\"Not;A=Brand\";v=\"99\", \"Microsoft Edge\";v=\"139\", \"Chromium\";v=\"139\"",
            "Sec-Ch-Ua-Mobile":"?0",
            "Sec-Ch-Ua-Platform":"\"Windows\"",
            "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"
        }
        base_url = "https://api.asmr-200.com"
        if trade_type == 'search':
            # 搜索场景
            url = base_url + "/api/works"
        elif trade_type == 'check':
            #检查场景
            url = base_url + "/api/workInfo/" + params
        else:
            url = base_url + "/api/workInfo/" + params
        async with self.http_session_proxy.get(url, params=params,headers=headers) as response:
            response.raise_for_status()
            logger.info(f"远端资源库返回HTTP STATUS: {response.status}")
            return await response.json()

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        """
        清理函数，用于关闭 aiohttp 客户端会话，释放资源。
        """
        if self.http_session_local and not self.http_session_local.closed:
            await self.http_session_local.close()
        if self.http_session_proxy and not self.http_session_proxy.closed:
            await self.http_session_proxy.close()
            logger.info("插件 [kikoeru_search] 已终止。")