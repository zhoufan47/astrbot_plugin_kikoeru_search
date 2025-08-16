import aiohttp
from astrbot.core.message.components import Image

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from .crawlers import kikoeru, neokikoeru


# 创建消息
def create_check_message(data:dict, base_url:str) -> str:
    reply_message = (
        f"✅ 查询成功！\n"
        f"--------------------\n"
        f"🎬 标题:{data.get('title')}\n"
        f"🔢 番号:{data.get('pid')}\n"
        f"📅 发行日:{data.get('release_date')}\n"
        f"🏢 制作组:{data.get('makers')}\n"
        f"🎤 演员:{data.get('artists')}\n"
        f"🎨 插画师:{data.get('illustrators')}\n"
        f"🏷️ 标签:{data.get('tags')}\n"
        f"💸 售价:{data.get('price')}\n"
        f"🏬 销量:{data.get('sales')}\n"
        f"🌟 评分:{data.get('rating')}/5\n"
        f"😃 评分人数:{data.get('rating_count')}\n"
        f"⛔ 年龄分级:{data.get('rate_grade')}\n"
        f"--------------------\n"
        f"{base_url}/work/{data.get('pid')}"
    )
    return reply_message


@register("kikoeru_search", "棒棒糖", "查询ASMR库数据", "1.1.0")
class MyPlugin(Star):

    ITEM_NOT_FOUND = "不存在"

    def __init__(self, context: Context,config: dict):
        super().__init__(context)
        #用来访问本地库的http_session
        self.http_session_local = None
        #用来访问ASMR.ONE的http_session,使用astrbot提供的代理信息
        self.http_session_proxy = None
        self.config = config
        #本地库地址
        self.api_url = config.get('api_url')
        #本地库cookies
        self.api_key = config.get('api_key')
        #本地库是否neokikoeru
        self.neokikoeru_flag = config.get('neokikoeru_flag',False)
        if not self.api_url or not self.api_key:
            logger.error("插件 [kikoeru_search] 的必要配置项 'api_url' 或 'api_key' 未填写，插件可能无法正常工作。")
        #asmr.one 的 cookies,默认一个无效cookies,非NSFW数据查询可用
        self.remote_key = config.get('remote_key',"1")
        #本地库的外部网络访问地址
        self.external_url = config.get('external_url',self.api_url)
        #查询远程ASMR库是是否检查本地库是否存在该作品
        self.check_local_flag = config.get('check_local_flag',False)
        self.remote_api_url = config.get('remote_api_url', 'https://api.asmr-200.com')
        self.remote_base_url = config.get('remote_base_url', 'https://asmr.one')
        logger.info("插件 [kikoeru_search] 已初始化。")

    async def initialize(self):
        self.http_session_local = aiohttp.ClientSession(trust_env=False)
        self.http_session_proxy = aiohttp.ClientSession(trust_env=True)
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("本地奥术")
    async def local_lib_search(self, event: AstrMessageEvent,query_str: str):
        logger.info(f"查询条件{query_str}")
        try:
            response = await self.query_local_repository("check", query_str)
            data = self.parse_local_result(response)
            if data.get("title",self.ITEM_NOT_FOUND) == self.ITEM_NOT_FOUND:
                yield event.plain_result(f"本地资源库不存在作品{query_str},可以下载！")
                return
            reply_message = create_check_message(data,self.external_url)
            yield event.plain_result(reply_message)
        except aiohttp.ClientResponseError as e:
            logger.error(f"插件 [kikoeru_search] 请求API时服务器返回错误: {e.status} {e.message}")
            yield event.plain_result(f"请求失败，服务器返回错误码：{e.status}")
        except Exception as e:
            logger.error(f"插件 [kikoeru_search] 处理命令 时发生未知错误: {e}", exc_info=True)
            yield event.plain_result("插件处理时发生未知错误，请联系管理员查看后台日志。")



    @filter.command("远程奥术")
    async def remote_lib_search(self, event: AstrMessageEvent,query_str: str):
        logger.info(f"查询条件: {query_str}")
        try:
            yield event.plain_result(f"开始查询远端资源库 {query_str} 的信息……")
            response = await self.query_remote_repository("check", query_str)
            #格式化ASMR库返回数据
            data = kikoeru.parse_result(response)
            name = data.get("title",self.ITEM_NOT_FOUND)  # 作品名称
            if name == self.ITEM_NOT_FOUND:
                yield event.plain_result(f"远端资源库不存在作品{query_str}，请确认番号是否正确")
                return

            #组装消息
            reply_message = create_check_message(data,self.remote_base_url)
            yield event.plain_result(reply_message)

            #处理封面
            main_cover_url = data.get("main_cover_url", "")
            if main_cover_url:
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
                response = await self.query_local_repository("check", query_str)
                data = self.parse_local_result(response)
                name = data.get("title", self.ITEM_NOT_FOUND)  # 作品名称
                if name == self.ITEM_NOT_FOUND:
                    yield event.plain_result(f"本地资源库不存在作品{query_str},可以下载！")
                else:
                    yield event.plain_result(f"本地资源库已存在作品{query_str}\n"
                                             f" {self.external_url}/work/{query_str}")
        except aiohttp.ClientResponseError as e:
            logger.error(f"插件 [kikoeru_search] 请求API时服务器返回错误: {e.status} {e.message}")
            yield event.plain_result(f"请求失败，服务器返回错误码：{e.status}")
        except Exception as e:
            logger.error(f"插件 [kikoeru_search] 处理命令 时发生未知错误: {e}", exc_info=True)
            yield event.plain_result("插件处理时发生未知错误，请联系管理员查看后台日志。")

    #格式化本地库查询结果
    def parse_local_result(self, response):
        if self.neokikoeru_flag:
            data = neokikoeru.parse_result(response)
        else:
            data = kikoeru.parse_result(response)
        return data

    async def query_local_repository(self,trade_type:str,params:str) -> dict:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "authorization":f"Bearer {self.api_key}",
        }
        request_params = params if trade_type == 'search' else None
        base_url = self.api_url.rstrip('/')
        if self.neokikoeru_flag:
            base_url= base_url + "/api/v1"
        else:
            base_url = base_url + "/api"
        if trade_type == 'search':
            # 搜索场景
            url = f"{base_url}/works"
            logger.info(f"搜索场景，条件 {params}")
        elif trade_type == 'check':
            #检查场景
            url = f"{base_url}/work/{params}"
            logger.info(f"检测场景，条件 {params}")
        else:
            url = f"{base_url}/work/{params}"
            logger.info(f"未知场景，默认为检查场景，条件 {params}")

        async with self.http_session_local.get(url, params=request_params,headers=headers) as response:
            logger.info(f"HTTP STATUS: {response.status}")
            if response.status == 404:
                return {"id":self.ITEM_NOT_FOUND}
            response.raise_for_status()
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
        base_url = self.remote_api_url.rstrip('/')
        request_params = params if trade_type == 'search' else None
        if trade_type == 'search':
            # 搜索场景
            url = f"{base_url}/api/works"
            logger.info(f"搜索场景，条件 {params}")
        elif trade_type == 'check':
            #检查场景
            url = f"{base_url}/api/workInfo/{params}"
            logger.info(f"检测场景，条件 {params}")
        else:
            url = f"{base_url}/api/workInfo/{params}"
            logger.info(f"未知场景，默认为检查场景，条件 {params}")
        async with self.http_session_proxy.get(url, params=request_params,headers=headers) as response:
            logger.info(f"远端资源库返回HTTP STATUS: {response.status}")
            if response.status == 404:
                return {"title":self.ITEM_NOT_FOUND}
            response.raise_for_status()
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