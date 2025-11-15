#!/usr/bin/env python3
"""
EvoVerse Literature System Complete Test Script

展示完整的文献爬取、结构化提取、存储和展示流程
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add EvoVerse to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def display_paper_metadata(paper, index: int = 0):
    """完整展示论文元数据结构"""
    print(f"\n{'='*80}")
    print(f"📄 论文 {index + 1}: {paper.title}")
    print(f"{'='*80}")
    
    # 基本标识信息
    print("🔖 标识信息:")
    print(f"  • ID: {paper.id}")
    print(f"  • 来源: {paper.source.value}")
    if paper.doi:
        print(f"  • DOI: {paper.doi}")
    if paper.arxiv_id:
        print(f"  • arXiv ID: {paper.arxiv_id}")
    if paper.pubmed_id:
        print(f"  • PubMed ID: {paper.pubmed_id}")
    
    # 作者信息
    if paper.authors:
        print(f"\n👥 作者信息 ({len(paper.authors)} 人):")
        for i, author in enumerate(paper.authors[:5], 1):  # 显示前5个作者
            affiliation = f" ({author.affiliation})" if author.affiliation else ""
            email = f" <{author.email}>" if author.email else ""
            print(f"  {i}. {author.name}{affiliation}{email}")
        if len(paper.authors) > 5:
            print(f"  ... 还有 {len(paper.authors) - 5} 位作者")
    
    # 出版信息
    print("📅 出版信息:")    
    if paper.publication_date:
        print(f"  • 发表日期: {paper.publication_date.strftime('%Y-%m-%d')}")
    if paper.year:
        print(f"  • 年份: {paper.year}")
    if paper.journal:
        print(f"  • 期刊: {paper.journal}")
    if paper.venue:
        print(f"  • 会议/场所: {paper.venue}")
    
    # 链接资源
    print("🔗 资源链接:")
    if paper.url:
        print(f"  • 页面链接: {paper.url}")
    if paper.pdf_url:
        print(f"  • PDF链接: {paper.pdf_url}")
    
    # 引用影响力
    print("📊 引用统计:")
    print(f"  • 总引用数: {paper.citation_count}")
    print(f"  • 参考文献数: {paper.reference_count}")
    print(f"  • 有影响力引用数: {paper.influential_citation_count}")
    
    # 研究领域和关键词
    if paper.fields:
        print(f"\n🏷️ 研究领域 ({len(paper.fields)} 个):")
        for field in paper.fields[:5]:
            print(f"  • {field}")
        if len(paper.fields) > 5:
            print(f"  ... 还有 {len(paper.fields) - 5} 个领域")
    
    if paper.keywords:
        print(f"\n🔑 关键词 ({len(paper.keywords)} 个):")
        print(f"  • {', '.join(paper.keywords[:10])}")
        if len(paper.keywords) > 10:
            print(f"  ... 还有 {len(paper.keywords) - 10} 个关键词")
    
    # 摘要
    if paper.abstract:
        print("📝 摘要:")        # 限制摘要长度以保持可读性
        abstract_preview = paper.abstract[:500] + "..." if len(paper.abstract) > 500 else paper.abstract
        print(f"  {abstract_preview}")
    
    # 全文（如果有的话）
    if paper.full_text:
        print("📖 全文预览:")
        text_preview = paper.full_text[:300] + "..." if len(paper.full_text) > 300 else paper.full_text
        print(f"  {text_preview}")
        print(f"  📏 总字数: {len(paper.full_text)}")

def test_complete_literature_workflow():
    """完整的文献工作流测试"""
    print("🚀 开始完整的 EvoVerse 文献系统测试\n")
    
    try:
        # 1. 导入所有必要模块
        print("📦 步骤1: 导入模块...")
        from evoverse.literature import (
            UnifiedLiteratureSearch, 
            ReferenceManager, 
            PDFExtractor,
            PaperSource
        )
        print("✅ 模块导入成功")
        
        # 2. 创建统一搜索器
        print("\n🔍 步骤2: 初始化统一搜索器...")
        searcher = UnifiedLiteratureSearch(
            arxiv_enabled=True,
            semantic_scholar_enabled=True,
            pubmed_enabled=False,  # 先禁用PubMed避免API限制
            # max_results_per_source=3  # 每个源限制3篇
        )
        print("✅ 搜索器初始化完成")
        
        # 3. 执行文献搜索
        query = "large language models transformers"
        print(f"\n📚 步骤3: 执行文献搜索 - 查询: '{query}'")
        
        papers = searcher.search(
            query=query,
            max_results_per_source=3,
            extract_full_text=False  # 先不提取全文，节省时间
        )
        
        print(f"✅ 搜索完成，共获取 {len(papers)} 篇论文")
        
        # 4. 详细展示每篇论文的结构化信息
        print("📋 步骤4: 展示结构化提取结果...")
        for i, paper in enumerate(papers):
            display_paper_metadata(paper, i)
        
        # 5. 创建参考文献管理器并存储
        if papers:
            print("💾 步骤5: 创建参考文献库并持久化...")
            manager = ReferenceManager(storage_path="test_complete_library.json")

            # 添加论文到库
            ref_ids = manager.add_references(papers)
            print(f"✅ 成功添加 {len(ref_ids)} 篇论文到参考文献库")
            
            # 显示库统计
            stats = manager.get_statistics()
            print(f"📊 库统计信息:")
            print(f"  • 总论文数: {stats['total_count']}")
            print(f"  • 包含DOI: {stats['doi_count']}")
            print(f"  • arXiv论文: {stats['arxiv_count']}")
            # print(f"  • Semantic Scholar论文: {stats['semantic_scholar_count']}")
            print(f"  • PubMed论文: {stats['pubmed_count']}")
            print(f"  • 引用链接数: {stats['citation_links']}")
            
            # 6. 测试PDF提取（如果有PDF链接）
            print("📄 步骤6: 测试PDF提取...")
            extractor = PDFExtractor()
            pdf_extracted_count = 0
            
            for paper in papers[:2]:  # 只测试前2篇
                if paper.pdf_url:
                    print(f"📥 尝试提取PDF: {paper.pdf_url}")
                    text = extractor.extract_from_url(
                        paper.pdf_url, 
                        paper_id=paper.primary_identifier
                    )
                    if text:
                        print(f"✅ PDF提取成功，获得 {len(text)} 字符文本")
                        pdf_extracted_count += 1
                        
                        # 显示文本预览
                        preview = text[:200] + "..." if len(text) > 200 else text
                        print(f"📖 文本预览: {preview}")
                    else:
                        print("❌ PDF提取失败")
            
            if pdf_extracted_count > 0:
                print(f"🎉 共成功提取 {pdf_extracted_count} 篇PDF")
            else:
                print("ℹ️  无可用PDF链接或提取失败")
        
        # 7. 显示缓存统计
        print("📊 步骤7: 显示缓存统计..." )
        from evoverse.literature import get_cache
        cache = get_cache()
        stats = cache.get_stats()
        
        print(f"💾 缓存系统状态:")
        print(f"  • 缓存目录: {stats['cache_dir']}")
        print(f"  • 总条目数: {stats['total_entries']}")
        print(f"  • 缓存大小: {stats['size_mb']:.2f} MB")
        print(f"  • 过期条目: {stats['expired_entries']}")
        print(f"  • TTL设置: {stats['ttl_hours']} 小时")
        
        # 8. 显示文件系统状态
        print("🗂️ 步骤8: 检查生成的文件...")
        files_to_check = [
            "test_complete_library.json",
            ".literature_cache"
        ]
        
        for file_path in files_to_check:
            path = Path(file_path)
            if path.exists():
                if path.is_file():
                    size_mb = path.stat().st_size / (1024 * 1024)
                    print(f"✅ 文件存在: {file_path} ({size_mb:.2f} MB)")
                else:
                    # 计算目录大小
                    total_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
                    size_mb = total_size / (1024 * 1024)
                    print(f"✅ 目录存在: {file_path} ({size_mb:.2f} MB)")
            else:
                print(f"❌ 文件不存在: {file_path}")
        
        # 9. 导出为其他格式
        if papers:
            print("📤 步骤9: 导出参考文献...")
            from evoverse.literature import papers_to_bibtex, papers_to_ris
            
            # BibTeX导出
            papers_to_bibtex(papers, "test_export.bib")
            print("✅ 导出 BibTeX: test_export.bib")
            
            # RIS导出
            papers_to_ris(papers, "test_export.ris")
            print("✅ 导出 RIS: test_export.ris")
            
            # JSON导出
            with open("test_export.json", "w", encoding="utf-8") as f:
                json.dump([paper.to_dict() for paper in papers], f, indent=2, ensure_ascii=False)
            print("✅ 导出 JSON: test_export.json")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_files():
    """清理测试文件"""
    test_files = [
        "test_complete_library.json",
        "test_export.bib",
        "test_export.ris", 
        "test_export.json"
    ]
    
    cleaned = 0
    for file_path in test_files:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            cleaned += 1
    
    # 清理PDF缓存（可选）
    pdf_cache = Path(".literature_cache/pdfs")
    if pdf_cache.exists():
        for pdf_file in pdf_cache.glob("*.pdf"):
            pdf_file.unlink()
            cleaned += 1
    
    print(f"🧹 清理了 {cleaned} 个测试文件")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EvoVerse 文献系统完整测试")
    parser.add_argument("--cleanup", action="store_true", help="清理测试文件")
    parser.add_argument("--query", default="large language models transformers", help="搜索查询")
    parser.add_argument("--max-results", type=int, default=3, help="每源最大结果数")
    
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_test_files()
        return
    
    print("🎯 EvoVerse 文献系统完整测试")
    print("=" * 80)
    
    # 运行完整测试
    success = test_complete_literature_workflow()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 测试完成！所有功能正常工作")
        print("\n📝 生成的文件:")
        print("  • test_complete_library.json - 参考文献库")
        print("  • test_export.bib - BibTeX格式")
        print("  • test_export.ris - RIS格式")
        print("  • test_export.json - JSON格式")
        print("  • .literature_cache/ - API缓存目录")
        
        print("\n🧹 运行以下命令清理测试文件:")
        print("  python test_complete_literature.py --cleanup")
    else:
        print("❌ 测试失败，请检查配置和依赖")

if __name__ == "__main__":
    main()