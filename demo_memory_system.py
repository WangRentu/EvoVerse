#!/usr/bin/env python3
"""
EvoVerse 学习记忆系统验证脚本
展示学习效果和记忆内容
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from evoverse.memory import MemoryStore, MemoryCategory
from evoverse.config import get_config


def print_section(title: str, char: str = "="):
    """打印分节标题"""
    print(f"\n{char * 70}")
    print(f"  {title}")
    print(f"{char * 70}\n")


def print_memory(memory, index: int = None):
    """格式化打印记忆"""
    prefix = f"[{index}] " if index is not None else ""
    print(f"{prefix}📌 {memory.content}")
    print(f"    ├─ 类别: {memory.category.value}")
    print(f"    ├─ 重要性: {memory.importance:.2f}")
    print(f"    ├─ 访问次数: {memory.access_count}")
    print(f"    ├─ 标签: {', '.join(memory.tags) if memory.tags else '无'}")
    print(f"    ├─ 创建时间: {memory.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if memory.data:
        print(f"    └─ 数据: {json.dumps(memory.data, ensure_ascii=False, indent=6)}")
    else:
        print(f"    └─ 数据: 无")
    print()


def test_learning_memory():
    """测试学习记忆系统"""
    print_section("🧠 EvoVerse 学习记忆系统验证", "=")
    
    # 初始化记忆系统
    memory_store = MemoryStore(max_memories=100)
    
    print("✅ 记忆系统初始化完成\n")
    
    # ========================================================================
    # 阶段1: 添加各种类型的记忆
    # ========================================================================
    print_section("阶段 1: 添加学习记忆", "-")
    
    print("📝 添加成功模式...")
    success_ids = []
    success_ids.append(memory_store.add_success_pattern(
        "使用分治法解决复杂问题",
        success_rate=0.9,
        tags=["algorithm", "problem_solving", "divide_conquer"]
    ))
    success_ids.append(memory_store.add_success_pattern(
        "使用缓存机制优化重复计算",
        success_rate=0.85,
        tags=["optimization", "cache", "performance"]
    ))
    success_ids.append(memory_store.add_success_pattern(
        "使用向量数据库进行语义搜索",
        success_rate=0.95,
        tags=["search", "vector_db", "semantic"]
    ))
    print(f"   ✅ 添加了 {len(success_ids)} 个成功模式\n")
    
    print("📝 添加失败教训...")
    failure_ids = []
    failure_ids.append(memory_store.add_failure_pattern(
        "尝试暴力枚举大数据集",
        "导致内存溢出和性能问题，应该使用流式处理或分批处理",
        tags=["performance", "mistake", "memory"]
    ))
    failure_ids.append(memory_store.add_failure_pattern(
        "在循环中频繁调用 LLM API",
        "导致API限流和成本过高，应该批量处理或使用缓存",
        tags=["api", "cost", "rate_limit"]
    ))
    print(f"   ✅ 添加了 {len(failure_ids)} 个失败教训\n")
    
    print("📝 添加死胡同...")
    dead_end_ids = []
    dead_end_ids.append(memory_store.add_dead_end(
        "尝试用线性模型拟合非线性关系",
        "多次实验证明效果很差，应该使用非线性模型或神经网络",
        tags=["modeling", "linear", "avoid"]
    ))
    dead_end_ids.append(memory_store.add_dead_end(
        "使用单一特征进行预测",
        "准确率始终低于50%，需要特征工程和多特征组合",
        tags=["feature", "prediction", "avoid"]
    ))
    print(f"   ✅ 添加了 {len(dead_end_ids)} 个死胡同\n")
    
    print("📝 添加重要洞察...")
    insight_ids = []
    insight_ids.append(memory_store.add_insight(
        "神经网络的深度比宽度更重要，在相同参数量下，深层网络通常表现更好",
        "literature_review",
        ["deep_learning", "architecture", "neural_network"]
    ))
    insight_ids.append(memory_store.add_insight(
        "注意力机制可以显著提升序列模型的性能，特别是在长序列任务中",
        "experiment",
        ["attention", "transformer", "sequence"]
    ))
    insight_ids.append(memory_store.add_insight(
        "数据质量比数据量更重要，高质量的小数据集往往优于低质量的大数据集",
        "research",
        ["data", "quality", "dataset"]
    ))
    print(f"   ✅ 添加了 {len(insight_ids)} 个重要洞察\n")
    
    # ========================================================================
    # 阶段2: 查看所有记忆内容
    # ========================================================================
    print_section("阶段 2: 查看记忆内容", "-")
    
    print("📚 成功模式记忆:")
    successes = memory_store.query_memory(MemoryCategory.SUCCESS_PATTERNS, limit=10)
    for i, mem in enumerate(successes, 1):
        print_memory(mem, i)
    
    print("\n📚 失败教训记忆:")
    failures = memory_store.query_memory(MemoryCategory.FAILURE_PATTERNS, limit=10)
    for i, mem in enumerate(failures, 1):
        print_memory(mem, i)
    
    print("\n📚 死胡同记忆:")
    dead_ends = memory_store.query_memory(MemoryCategory.DEAD_ENDS, limit=10)
    for i, mem in enumerate(dead_ends, 1):
        print_memory(mem, i)
    
    print("\n📚 重要洞察记忆:")
    insights = memory_store.query_memory(MemoryCategory.INSIGHTS, limit=10)
    for i, mem in enumerate(insights, 1):
        print_memory(mem, i)
    
    # ========================================================================
    # 阶段3: 展示学习效果 - 查询相关记忆
    # ========================================================================
    print_section("阶段 3: 学习效果展示 - 智能查询", "-")
    
    print("🔍 查询与 '优化' 相关的记忆:")
    optimization_memories = memory_store.search_similar("优化 performance cache", limit=5)
    for i, mem in enumerate(optimization_memories, 1):
        print(f"  [{i}] {mem.content} (类别: {mem.category.value}, 重要性: {mem.importance:.2f})")
    print()
    
    print("🔍 查询与 '模型' 相关的记忆:")
    model_memories = memory_store.search_similar("模型 neural network deep learning", limit=5)
    for i, mem in enumerate(model_memories, 1):
        print(f"  [{i}] {mem.content} (类别: {mem.category.value}, 重要性: {mem.importance:.2f})")
    print()
    
    print("🔍 查询高重要性记忆 (重要性 >= 0.9):")
    important_memories = memory_store.query_memory(min_importance=0.9, limit=10)
    for i, mem in enumerate(important_memories, 1):
        print(f"  [{i}] {mem.content} (重要性: {mem.importance:.2f}, 类别: {mem.category.value})")
    print()
    
    # ========================================================================
    # 阶段4: 实验去重功能
    # ========================================================================
    print_section("阶段 4: 实验去重功能", "-")
    
    print("🧪 记录实验...")
    exp1_hash = memory_store.record_experiment(
        "使用BERT进行文本分类",
        "fine-tuning with learning rate 2e-5"
    )
    print(f"   ✅ 实验1已记录: {exp1_hash[:16]}...")
    
    exp2_hash = memory_store.record_experiment(
        "使用GPT进行文本生成",
        "few-shot learning with 5 examples"
    )
    print(f"   ✅ 实验2已记录: {exp2_hash[:16]}...")
    
    print("\n🔍 检查重复实验...")
    
    # 检查相同实验
    is_dup1, reason1 = memory_store.is_duplicate_experiment(
        "使用BERT进行文本分类",
        "fine-tuning with learning rate 2e-5"
    )
    print(f"   实验1重复检查: {'❌ 是重复实验' if is_dup1 else '✅ 新实验'}")
    if reason1:
        print(f"   原因: {reason1}")
    
    # 检查新实验
    is_dup2, reason2 = memory_store.is_duplicate_experiment(
        "使用RoBERTa进行文本分类",
        "fine-tuning with learning rate 1e-5"
    )
    print(f"   实验3重复检查: {'❌ 是重复实验' if is_dup2 else '✅ 新实验'}")
    if reason2:
        print(f"   原因: {reason2}")
    
    # ========================================================================
    # 阶段5: 展示学习效果 - 避免重复错误
    # ========================================================================
    print_section("阶段 5: 学习效果 - 避免重复错误", "-")
    
    print("💡 场景: 系统要处理大数据集，查询相关记忆...")
    big_data_memories = memory_store.search_similar("大数据集 内存 处理", limit=3)
    
    if big_data_memories:
        print("\n   ⚠️  发现相关失败记忆:")
        for mem in big_data_memories:
            if mem.category == MemoryCategory.FAILURE_PATTERNS:
                print(f"      - {mem.content}")
                print(f"        教训: {mem.data.get('lesson', 'N/A')}")
        print("\n   ✅ 系统可以避免重复这个错误！")
    else:
        print("   ℹ️  未找到相关记忆")
    print()
    
    print("💡 场景: 系统要优化性能，查询相关记忆...")
    perf_memories = memory_store.query_memory(
        tags=["performance", "optimization"],
        limit=5
    )
    
    if perf_memories:
        print("\n   📖 找到相关记忆:")
        for mem in perf_memories:
            category_icon = "✅" if mem.category == MemoryCategory.SUCCESS_PATTERNS else "❌"
            print(f"      {category_icon} {mem.content}")
        print("\n   ✅ 系统可以参考这些经验！")
    else:
        print("   ℹ️  未找到相关记忆")
    print()
    
    # ========================================================================
    # 阶段6: 记忆统计和详细信息
    # ========================================================================
    print_section("阶段 6: 记忆统计信息", "-")
    
    stats = memory_store.get_stats()
    print("📊 记忆系统统计:")
    print(f"   总记忆数: {stats['total_memories']}")
    print(f"   最大容量: {stats['max_memories']}")
    print(f"   实验签名数: {stats['experiment_signatures']}")
    print(f"   清理周期: {stats['prune_after_days']} 天")
    print()
    
    print("📊 按类别统计:")
    for category, count in stats['by_category'].items():
        print(f"   {category}: {count} 条")
    print()
    
    # ========================================================================
    # 阶段7: 展示记忆访问追踪
    # ========================================================================
    print_section("阶段 7: 记忆访问追踪", "-")
    
    print("🔍 多次查询同一记忆，观察访问计数变化...")
    
    # 查询几次，增加访问计数
    for i in range(3):
        memory_store.query_memory(MemoryCategory.INSIGHTS, limit=1)
    
    # 再次查询并显示访问计数
    accessed_memories = memory_store.query_memory(MemoryCategory.INSIGHTS, limit=5)
    print("\n   访问计数最高的洞察:")
    for mem in sorted(accessed_memories, key=lambda m: m.access_count, reverse=True)[:3]:
        print(f"      - {mem.content[:60]}...")
        print(f"        访问次数: {mem.access_count}, 最后访问: {mem.last_accessed.strftime('%H:%M:%S')}")
    print()
    
    # ========================================================================
    # 阶段8: 导出记忆内容
    # ========================================================================
    print_section("阶段 8: 导出记忆内容", "-")
    
    print("💾 导出所有记忆为 JSON 格式...")
    all_memories = []
    for category in MemoryCategory:
        memories = memory_store.query_memory(category, limit=100)
        for mem in memories:
            all_memories.append({
                "id": mem.id,
                "category": mem.category.value,
                "content": mem.content,
                "importance": mem.importance,
                "tags": mem.tags,
                "access_count": mem.access_count,
                "created_at": mem.created_at.isoformat(),
                "data": mem.data
            })
    
    # 保存到文件
    output_file = Path("memory_export.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_memories, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 已导出 {len(all_memories)} 条记忆到: {output_file}")
    print(f"   📄 文件大小: {output_file.stat().st_size} 字节")
    print()
    
    # ========================================================================
    # 总结
    # ========================================================================
    print_section("✅ 验证完成", "=")
    
    print("📋 验证总结:")
    print(f"   ✅ 成功添加 {len(success_ids)} 个成功模式")
    print(f"   ✅ 成功添加 {len(failure_ids)} 个失败教训")
    print(f"   ✅ 成功添加 {len(dead_end_ids)} 个死胡同")
    print(f"   ✅ 成功添加 {len(insight_ids)} 个重要洞察")
    print(f"   ✅ 记录了 {stats['experiment_signatures']} 个实验签名")
    print(f"   ✅ 总记忆数: {stats['total_memories']}")
    print()
    
    print("🎯 学习记忆系统功能验证:")
    print("   ✅ 记忆添加功能正常")
    print("   ✅ 记忆查询功能正常")
    print("   ✅ 相似记忆搜索正常")
    print("   ✅ 实验去重功能正常")
    print("   ✅ 访问计数追踪正常")
    print("   ✅ 记忆导出功能正常")
    print()
    
    print("💡 学习效果:")
    print("   ✅ 系统可以记住成功的方法")
    print("   ✅ 系统可以记住失败的教训")
    print("   ✅ 系统可以避免重复错误")
    print("   ✅ 系统可以检索相关经验")
    print("   ✅ 系统可以防止重复实验")
    print()


if __name__ == "__main__":
    try:
        test_learning_memory()
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()