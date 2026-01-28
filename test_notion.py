#!/usr/bin/env python3
"""
Notion API测试脚本
测试Integration Token和Database ID是否可用
"""

from notion_client import Client, APIResponseError
import sys

def print_step(step_num, description):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"步骤 {step_num}: {description}")
    print('='*60)

def print_success(message):
    """打印成功信息"""
    print(f"✅ {message}")

def print_error(message):
    """打印错误信息"""
    print(f"❌ {message}")

def print_info(message):
    """打印信息"""
    print(f"ℹ️  {message}")

def get_user_input(prompt, default=None):
    """获取用户输入"""
    if default:
        return input(f"{prompt} (默认: {default}): ") or default
    return input(f"{prompt}: ")

def validate_token_format(token):
    """验证Token格式"""
    if not token.startswith("secret_"):
        print_error("Token格式不正确！应该以'secret_'开头")
        return False
    if len(token) < 50:
        print_error("Token太短！可能不完整")
        return False
    return True

def validate_database_id(database_id):
    """验证Database ID格式"""
    # Notion database ID是32位，可能有连字符
    cleaned = database_id.replace("-", "")
    if len(cleaned) != 32:
        print_error(f"Database ID格式不正确！应该是32位字符，当前是{len(cleaned)}位")
        return False
    return True

def test_token(token):
    """测试Token是否有效"""
    print_step(1, "测试Integration Token")
    
    try:
        print_info("正在连接Notion API...")
        client = Client(auth=token)
        
        # 尝试获取用户信息来验证token
        user = client.users.me()
        print_success(f"Token有效！连接的用户: {user['name']} ({user['type']})")
        print_info(f"用户ID: {user['id']}")
        
        return client
        
    except APIResponseError as e:
        print_error(f"Token无效或已过期")
        print_info(f"错误详情: {e}")
        return None
    except Exception as e:
        print_error(f"连接失败: {e}")
        return None

def test_database(client, database_id):
    """测试Database是否可访问"""
    print_step(2, "测试Database访问")
    
    if not validate_database_id(database_id):
        return False
    
    try:
        print_info(f"正在查询Database: {database_id}")
        
        # 尝试获取database信息
        database = client.databases.retrieve(database_id)
        
        print_success(f"成功访问Database！")
        print_info(f"Database标题: {database['title'][0]['plain_text']}")
        
        # 打印数据库属性
        print("\nDatabase属性:")
        if 'properties' in database:
            for prop_name, prop_info in database['properties'].items():
                prop_type = prop_info['type']
                print(f"  • {prop_name} ({prop_type})")
        
        # 查询数据库中的记录数
        query_result = client.databases.query(database_id=database_id)
        total_count = len(query_result['results'])
        print_success(f"Database当前包含 {total_count} 条记录")
        
        if total_count > 0:
            print("\n最近3条记录:")
            for i, page in enumerate(query_result['results'][:3], 1):
                title = page['properties'].get('title', {}).get('title', [{}])[0].get('plain_text', '无标题')
                created_time = page['created_time']
                print(f"  {i}. {title} (创建时间: {created_time})")
        
        return True
        
    except APIResponseError as e:
        error_code = e.code
        error_message = e.message
        
        if error_code == "object_not_found":
            print_error("Database不存在或ID错误")
            print_info("请检查:")
            print_info("  1. Database ID是否正确（32位）")
            print_info("  2. Database是否已删除")
            print_info("  3. 您是否有权访问这个Database")
        elif error_code == "unauthorized":
            print_error("未授权访问此Database")
            print_info("请确保:")
            print_info("  1. 在Database设置中添加了Integration连接")
            print_info("  2. Integration有正确的权限（Read content, Insert content）")
        else:
            print_error(f"访问Database失败")
            print_info(f"错误代码: {error_code}")
            print_info(f"错误信息: {error_message}")
        
        return False
    except Exception as e:
        print_error(f"查询Database失败: {e}")
        return False

def test_create_page(client, database_id):
    """测试创建页面（可选）"""
    print_step(3, "测试创建测试页面（可选）")
    
    create_test = input("是否创建测试页面来验证写入权限？(y/n): ").lower()
    if create_test != 'y':
        print_info("跳过创建测试页面")
        return True
    
    try:
        print_info("正在创建测试页面...")
        
        from datetime import datetime
        
        page = client.pages.create(
            parent={"database_id": database_id},
            properties={
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": f"🧪 Notion API测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        }
                    ]
                }
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "恭喜！Notion API集成测试成功！🎉"}
                            }
                        ]
                    }
                }
            ]
        )
        
        print_success("测试页面创建成功！")
        print_info(f"页面ID: {page['id']}")
        print_info(f"页面URL: https://www.notion.so/{page['id'].replace('-', '')}")
        
        return True
        
    except APIResponseError as e:
        print_error(f"创建页面失败")
        print_info(f"错误代码: {e.code}")
        print_info(f"错误信息: {e.message}")
        return False
    except Exception as e:
        print_error(f"创建页面失败: {e}")
        return False

def main():
    """主函数"""
    print("""
╔═════════════════════════════════════════════════════════╗
║            Notion API 集成测试工具                        ║
║                                                            ║
║  这个脚本将测试您的 Notion Integration Token 和          ║
║  Database ID 是否配置正确                                 ║
╚═════════════════════════════════════════════════════════╝
""")
    
    # 获取用户输入
    print("\n请输入您的Notion配置信息:")
    print("(您可以从环境变量或命令行参数获取这些信息)")
    print()
    
    token = input("请输入 Notion Integration Token: ").strip()
    if not token:
        print_error("Token不能为空！")
        sys.exit(1)
    
    database_id = input("请输入 Database ID: ").strip()
    if not database_id:
        print_error("Database ID不能为空！")
        sys.exit(1)
    
    # 测试Token
    client = test_token(token)
    if not client:
        print("\n" + "="*60)
        print("❌ 测试失败！请检查您的Token")
        print("="*60)
        sys.exit(1)
    
    # 测试Database
    database_ok = test_database(client, database_id)
    if not database_ok:
        print("\n" + "="*60)
        print("❌ Database访问测试失败！")
        print("="*60)
        sys.exit(1)
    
    # 测试创建页面
    write_ok = test_create_page(client, database_id)
    
    # 总结
    print("\n" + "="*60)
    print("🎉 测试完成！")
    print("="*60)
    
    print("\n✅ Token: 有效")
    print("✅ Database: 可访问")
    if write_ok:
        print("✅ 写入权限: 正常")
    
    print("\n📝 您的配置信息:")
    print(f"  Token: {token[:20]}...{token[-10:]}")
    print(f"  Database ID: {database_id}")
    
    print("\n💡 下一步:")
    print("  1. 将这些信息保存到 .env 文件:")
    print("     NOTION_TOKEN=" + token)
    print("     NOTION_DATABASE_ID=" + database_id)
    print("  2. 确保您的Database有以下属性:")
    print("     - Title (Title类型)")
    print("     - Genre (Select类型)")
    print("     - Status (Select类型)")
    print("     - CreatedAt (Date类型)")
    print("     - WordCount (Number类型)")
    print("  3. 开始使用Story Agent！")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生意外错误: {e}")
        sys.exit(1)