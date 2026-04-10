#!/usr/bin/env python3
"""
API密钥管理助手
用途：简化DashScope API密钥的安全管理和轮换
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List


class APIKeyManager:
    """API密钥管理器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.env_file = self.project_root / ".env"
        self.env_local_file = self.project_root / ".env.local"
        self.env_example = self.project_root / ".env.example"
        self.env_local_example = self.project_root / ".env.local.example"
        self.gitignore = self.project_root / ".gitignore"
        self.key_history_file = self.project_root / ".key_rotation_history.json"

    def read_env_file(self, filepath: Path) -> Optional[str]:
        """读取环境变量文件"""
        if filepath.exists():
            return filepath.read_text()
        return None

    def write_env_file(self, filepath: Path, content: str) -> bool:
        """写入环境变量文件"""
        try:
            filepath.write_text(content)
            # 设置文件权限为600（仅所有者可读写）
            filepath.chmod(0o600)
            return True
        except Exception as e:
            print(f"❌ 写入失败: {e}")
            return False

    def get_current_key(self) -> Optional[str]:
        """获取当前的API密钥"""
        for env_file in [self.env_local_file, self.env_file]:
            if content := self.read_env_file(env_file):
                match = re.search(r"DASHSCOPE_API_KEY=(.+?)(?:\n|$)", content)
                if match:
                    key = match.group(1).strip("\"'")
                    if key and key != "your_dashscope_api_key_here_for_local_dev":
                        return key
        return None

    def update_key(self, new_key: str, env_type: str = "local") -> bool:
        """更新API密钥"""

        if env_type == "local":
            target_file = self.env_local_file
            template_file = self.env_local_example
        else:
            target_file = self.env_file
            template_file = self.env_example

        # 如果目标文件不存在，从模板创建
        if not target_file.exists():
            if template_file.exists():
                content = self.read_env_file(template_file)
            else:
                print(f"❌ 找不到模板文件: {template_file}")
                return False
        else:
            content = self.read_env_file(target_file)

        # 替换或添加密钥
        if "DASHSCOPE_API_KEY" in content:
            content = re.sub(
                r"DASHSCOPE_API_KEY=.*", f"DASHSCOPE_API_KEY={new_key}", content
            )
        else:
            content += f"\nDASHSCOPE_API_KEY={new_key}\n"

        if self.write_env_file(target_file, content):
            print(f"✅ 已更新 {target_file} 中的API密钥")
            self._record_rotation(new_key, env_type)
            return True
        return False

    def _record_rotation(self, new_key: str, env_type: str):
        """记录密钥轮换历史（仅记录密钥前缀和时间，不存储完整密钥）"""
        history = []

        if self.key_history_file.exists():
            try:
                history = json.loads(self.key_history_file.read_text())
            except:
                history = []

        # 仅记录密钥前缀（安全起见）
        key_prefix = new_key[:7] + "..." if len(new_key) > 7 else "***"

        history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "env_type": env_type,
                "key_prefix": key_prefix,
            }
        )

        self.key_history_file.write_text(
            json.dumps(history, indent=2, ensure_ascii=False)
        )
        self.key_history_file.chmod(0o600)

    def check_gitignore(self) -> bool:
        """检查.gitignore是否正确配置"""
        if not self.gitignore.exists():
            print("⚠️ 未找到.gitignore文件")
            return False

        content = self.gitignore.read_text()
        required_patterns = [".env", ".env.local"]

        missing = []
        for pattern in required_patterns:
            if pattern not in content:
                missing.append(pattern)

        if missing:
            print(f"⚠️ .gitignore缺少以下模式: {', '.join(missing)}")
            return False

        print("✅ .gitignore配置正确")
        return True

    def check_git_excluded(self) -> bool:
        """检查.env文件是否在git中被正确忽略"""
        import subprocess

        try:
            # 检查.env是否被git忽略
            result = subprocess.run(
                ["git", "check-ignore", ".env", ".env.local"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ .env文件已被git正确忽略")
                return True
            else:
                print("❌ .env文件未被git忽略！")
                return False
        except Exception as e:
            print(f"⚠️ 检查git忽略失败: {e}")
            return False

    def validate_key_format(self, key: str) -> bool:
        """验证API密钥格式"""
        # DashScope密钥格式: sk-开头，后跟十六进制字符
        if re.match(r"^sk-[0-9a-f]{30,}$", key, re.IGNORECASE):
            return True
        return False

    def show_security_status(self):
        """显示安全状态"""
        print("\n" + "=" * 50)
        print("🔐 API密钥安全状态检查")
        print("=" * 50 + "\n")

        # 检查1: 当前密钥
        current_key = self.get_current_key()
        if current_key:
            key_display = (
                current_key[:7] + "..." + current_key[-4:]
                if len(current_key) > 11
                else "***"
            )
            print(f"✅ 已检测到当前API密钥: {key_display}")

            if self.validate_key_format(current_key):
                print("✅ 密钥格式有效")
            else:
                print("⚠️ 密钥格式可能无效")
        else:
            print("❌ 未找到配置的API密钥")

        # 检查2: .gitignore
        print()
        self.check_gitignore()

        # 检查3: Git忽略状态
        print()
        self.check_git_excluded()

        # 检查4: 密钥轮换历史
        if self.key_history_file.exists():
            history = json.loads(self.key_history_file.read_text())
            print(f"\n✅ 密钥轮换历史: {len(history)} 次记录")
            for entry in history[-3:]:  # 显示最后3次
                print(
                    f"  • {entry['timestamp']}: {entry['env_type']} - {entry['key_prefix']}"
                )
        else:
            print("\n📝 无密钥轮换历史")

        print("\n" + "=" * 50 + "\n")

    def interactive_rotate_key(self):
        """交互式密钥轮换"""
        print("\n" + "=" * 50)
        print("🔄 交互式API密钥轮换")
        print("=" * 50 + "\n")

        print("⚠️  在继续之前，请确保：")
        print("  1. 已从DashScope控制台撤销旧密钥")
        print("  2. 已生成新的API密钥")
        print("  3. 新密钥已保存到安全的地方")
        print()

        # 获取新密钥
        print("请输入新的DashScope API密钥 (或按Ctrl+C取消):")
        new_key = input("新API密钥: ").strip()

        if not new_key:
            print("❌ 密钥不能为空")
            return False

        # 验证格式
        if not self.validate_key_format(new_key):
            print("⚠️ 警告：密钥格式看起来不是DashScope格式")
            confirm = input("是否继续? (yes/no): ").strip().lower()
            if confirm != "yes":
                return False

        # 选择环保环境
        print("\n选择环境:")
        print("1. 本地开发环境 (.env.local) - 推荐")
        print("2. 项目环境 (.env)")
        choice = input("选择 (1/2): ").strip()

        env_type = "local" if choice == "1" else "prod"

        # 确认
        print()
        print(f"将更新 {env_type} 环境的API密钥")
        confirm = input("是否继续? (yes/no): ").strip().lower()

        if confirm == "yes":
            target_file = self.env_local_file if env_type == "local" else self.env_file
            if self.update_key(new_key, env_type):
                print(f"\n✅ 密钥已成功更新到 {target_file}")
                print("✅ 请确保:")
                print("  • 使用新密钥启动应用")
                print("  • 测试API连接")
                print("  • 删除旧密钥文件副本")
                return True
            else:
                print("\n❌ 密钥更新失败")
                return False
        else:
            print("❌ 已取消")
            return False


def main():
    """主函数"""

    print(
        """
╔═══════════════════════════════════════════════════════════╗
║         🔐 API密钥安全管理工具                           ║
║     DashScope API Key Security Manager                    ║
╚═══════════════════════════════════════════════════════════╝
    """
    )

    manager = APIKeyManager()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "status":
            manager.show_security_status()

        elif command == "rotate":
            manager.interactive_rotate_key()

        elif command == "check":
            manager.check_gitignore()
            manager.check_git_excluded()

        else:
            print(f"❌ 未知命令: {command}")
            show_help()

    else:
        # 交互模式菜单
        show_help()
        print("\n请选择操作:")
        print("1. 查看安全状态")
        print("2. 密钥轮换")
        print("3. 检查配置")
        print("4. 退出")

        choice = input("\n选择 (1-4): ").strip()

        if choice == "1":
            manager.show_security_status()
        elif choice == "2":
            manager.interactive_rotate_key()
        elif choice == "3":
            manager.check_gitignore()
            manager.check_git_excluded()
        else:
            print("👋 再见!")


def show_help():
    """显示帮助信息"""
    print(
        """
使用方法:
  python api_key_manager.py [命令]

命令:
  status    - 显示API密钥安全状态
  rotate    - 交互式密钥轮换
  check     - 检查gitignore配置
  
示例:
  python api_key_manager.py status      # 查看状态
  python api_key_manager.py rotate      # 开始轮换

📚 更多信息请查看: API_KEY_SECURITY.md
    """
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
