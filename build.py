import os
import sys
import subprocess
from pathlib import Path

def build_executable():
    print("=" * 60)
    print("智能笔记管理系统 - 构建脚本")
    print("=" * 60)
    print()
    
    project_root = Path(__file__).parent
    main_script = project_root / "gui.py"
    
    if not main_script.exists():
        print("错误: 找不到主程序文件 gui.py")
        return False
    
    print("检查 PyInstaller...")
    try:
        import PyInstaller
        print(f"✓ PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller 安装完成")
    
    print()
    print("开始构建可执行文件...")
    print()
    
    build_command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=SmartNotes",
        "--windowed",
        "--onefile",
        "--clean",
        "--noconfirm",
        str(main_script)
    ]
    
    try:
        print("执行构建命令:")
        print(" ".join(build_command))
        print()
        
        result = subprocess.run(build_command, check=True, cwd=str(project_root))
        
        print()
        print("=" * 60)
        print("✓ 构建成功！")
        print("=" * 60)
        print()
        
        dist_dir = project_root / "dist"
        if dist_dir.exists():
            print(f"可执行文件位置: {dist_dir}")
            print()
            print("生成的文件:")
            for file in dist_dir.iterdir():
                if file.is_file():
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"  - {file.name} ({size_mb:.2f} MB)")
        
        print()
        print("清理构建文件...")
        build_dir = project_root / "build"
        spec_file = project_root / "SmartNotes.spec"
        
        if build_dir.exists():
            import shutil
            shutil.rmtree(build_dir)
            print("✓ 已删除 build 目录")
        
        if spec_file.exists():
            spec_file.unlink()
            print("✓ 已删除 .spec 文件")
        
        print()
        print("=" * 60)
        print("构建完成！您可以在 dist 目录中找到可执行文件。")
        print("=" * 60)
        
        return True
    
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 60)
        print("✗ 构建失败")
        print("=" * 60)
        print(f"错误信息: {e}")
        return False
    
    except Exception as e:
        print()
        print("=" * 60)
        print("✗ 发生未知错误")
        print("=" * 60)
        print(f"错误信息: {e}")
        return False

def main():
    print()
    response = input("是否开始构建可执行文件？(y/n): ")
    
    if response.lower() in ['y', 'yes', '是']:
        success = build_executable()
        
        if success:
            print()
            input("按回车键退出...")
        else:
            print()
            input("构建失败，按回车键退出...")
            sys.exit(1)
    else:
        print("已取消构建")

if __name__ == "__main__":
    main()
