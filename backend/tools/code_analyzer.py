#最终执行的代码
import logging
from typing import Optional
from dataclasses import dataclass

import dashscope
from dashscope import Generation
from dashscope.api_entities.dashscope_response import GenerationResponse
from dashscope.exception import (
    ApiKeyNotFoundError,
    ApiKeyExpiredError,
    RateLimitExceededError,
    ServiceUnavailableError,
    BadRequestError
)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# ====================== 基础配置（复用之前的 AppConfig） ======================
@dataclass(frozen=True)
class AppConfig:
    dashscope_api_key: str
    qwen_model: str = "qwen-turbo"
    max_retry_attempts: int = 3
    max_tokens: int = 2000
    timeout: int = 30  # 新增超时配置

# ====================== 日志配置 ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ====================== 重试装饰器工厂函数（补全缺失逻辑） ======================
def create_retry_decorator(max_attempts: int):
    """创建通义千问 API 重试装饰器"""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=10),  # 2s→4s→8s 重试
        retry=retry_if_exception_type(
            (RateLimitExceededError, ServiceUnavailableError)  # 仅重试限流/服务不可用
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True  # 最终失败时抛出异常
    )

# ====================== 提示词加载函数（补全缺失逻辑） ======================
def load_prompt() -> str:
    """加载代码分析提示词（可扩展为从文件/配置中心加载）"""
    prompt_template = """
    你是资深 Python 工程师，请严格按照以下要求分析代码错误：
    
    待分析代码：
    {code}
    
    输出格式（必须严格遵守，分3部分）：
    1. 错误原因：清晰描述错误类型、出现位置、根本原因
    2. 修改方案：提供可直接运行的修正代码，并标注具体修改点
    3. 优化建议：从代码规范、性能、可读性角度给出额外建议
    """
    return prompt_template

# ====================== 核心分析类（优化后） ======================
class QwenCodeAnalyzer:
    """通义千问代码分析器（企业级实现）"""
    # 类常量：代码长度上限（避免 API 输入超限）
    MAX_CODE_LENGTH = 8000

    def __init__(self, config: AppConfig):
        """初始化分析器
        
        Args:
            config: 通义千问配置类（包含 API Key、模型名等）
        """
        self.config = config
        # 初始化通义千问 API Key
        dashscope.api_key = config.dashscope_api_key
        # 创建重试装饰器（绑定到实例）
        self.retry_decorator = create_retry_decorator(config.max_retry_attempts)
        # 绑定重试装饰器到 analyze 方法（核心：让重试生效）
        self.analyze = self.retry_decorator(self.analyze)
        logger.info(f"QwenCodeAnalyzer 初始化成功，模型: {config.qwen_model}")

    def validate_code(self, code: str) -> str:
        """校验代码输入有效性
        
        Args:
            code: 待分析的 Python 代码字符串
        
        Returns:
            str: 校验后的代码（去除首尾空格）
        
        Raises:
            ValueError: 代码为空或长度超限
            TypeError: 代码非字符串类型
        """
        if not isinstance(code, str):
            raise TypeError(f"代码必须是字符串类型，当前类型: {type(code)}")
        if not code:
            logger.error("代码输入为空")
            raise ValueError("code empty: 代码不能为空")
        if len(code) > self.MAX_CODE_LENGTH:
            logger.error(f"代码长度超限：当前 {len(code)} 字符，上限 {self.MAX_CODE_LENGTH} 字符")
            raise ValueError(f"code too long: 代码长度超过 {self.MAX_CODE_LENGTH} 字符")
        
        cleaned_code = code.strip()
        logger.info(f"代码校验通过，有效长度: {len(cleaned_code)} 字符")
        return cleaned_code

    def parse_response(self, resp: GenerationResponse) -> str:
        """解析通义千问 API 响应
        
        Args:
            resp: 通义千问 API 响应对象
        
        Returns:
            str: 解析后的分析结果
        
        Raises:
            RuntimeError: 响应状态码异常或内容为空
        """
        logger.info(f"开始解析 API 响应，状态码: {resp.status_code}")
        if resp.status_code != 200:
            error_msg = f"Qwen API error {resp.code}: {resp.message}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        if not resp.output or not resp.output.choices:
            error_msg = "Empty response: 通义千问返回空内容"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        result = resp.output.choices[0].message.content.strip()
        logger.info(f"响应解析成功，结果长度: {len(result)} 字符")
        return result

    def analyze(self, code: str) -> str:
        """核心方法：调用通义千问分析代码错误（已绑定重试装饰器）
        
        Args:
            code: 待分析的 Python 代码字符串
        
        Returns:
            str: 通义千问的代码分析结果
        
        Raises:
            ValueError: 代码校验失败
            ApiKeyNotFoundError/ApiKeyExpiredError: API Key 错误/过期
            RateLimitExceededError: API 限流
            RuntimeError: 响应解析失败
        """
        try:
            # 1. 校验代码
            cleaned_code = self.validate_code(code)
            
            # 2. 加载并渲染提示词
            prompt = load_prompt().format(code=cleaned_code)
            logger.info("提示词渲染完成，开始调用通义千问 API")
            
            # 3. 调用通义千问 API（补充超时配置）
            response = Generation.call(
                model=self.config.qwen_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout  # 新增超时配置
            )
            
            # 4. 解析响应
            return self.parse_response(response)
        
        # 捕获通义千问专属异常并补充日志
        except ApiKeyNotFoundError:
            logger.error("DASHSCOPE_API_KEY 未配置或无效")
            raise
        except ApiKeyExpiredError:
            logger.error("DASHSCOPE_API_KEY 已过期")
            raise
        except BadRequestError as e:
            logger.error(f"请求参数错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"代码分析核心逻辑异常: {str(e)}", exc_info=True)
            raise

# ====================== 测试调用 ======================
if __name__ == "__main__":
    # 配置示例（生产环境建议从环境变量加载）
    config = AppConfig(
        dashscope_api_key="你的通义千问API Key",
        qwen_model="qwen-turbo",
        max_retry_attempts=3
    )
    
    # 创建分析器实例
    analyzer = QwenCodeAnalyzer(config)
    
    # 测试错误代码
    test_code = """
    def add(a, b)
        return a + b
    print(add(1, 2))
    """
    
    # 调用分析方法
    try:
        result = analyzer.analyze(test_code)
        print("=== 通义千问代码分析结果 ===")
        print(result)
    except Exception as e:
        logger.error(f"测试调用失败: {str(e)}")