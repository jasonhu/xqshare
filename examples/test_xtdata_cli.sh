#!/bin/bash
# xtdata CLI 测试脚本 - 标准级别函数覆盖
#
# 用法:
#   ./test_xtdata_cli.sh                    # 默认: json格式, compact模式
#   ./test_xtdata_cli.sh --format text      # 使用 text 格式
#   ./test_xtdata_cli.sh --no-compact       # 不使用 compact 模式
#   ./test_xtdata_cli.sh --host 192.168.1.100 --port 18812
#   ./test_xtdata_cli.sh --limit 5          # 限制输出条数
#   ./test_xtdata_cli.sh --verbose          # 显示详细日志
#   ./test_xtdata_cli.sh --skip-download    # 跳过下载步骤
#   ./test_xtdata_cli.sh --only basic       # 只运行 basic 级别测试
#   ./test_xtdata_cli.sh --exclude tick     # 排除 tick 级别测试

set -e

# ==================== 默认参数 ====================
HOST="${XQSHARE_REMOTE_HOST:-localhost}"
PORT="${XQSHARE_REMOTE_PORT:-18812}"
FORMAT="json"
COMPACT="--compact"
LIMIT=""
VERBOSE=""
SKIP_DOWNLOAD=false
ONLY=""
EXCLUDE=""
STOCK="000001.SZ"
STOCK2="600000.SH"
STOCK3="000002.SZ"
STOCK4="600519.SH"
FULL_OUTPUT=false

# ==================== 解析参数 ====================
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --format|-f)
            FORMAT="$2"
            shift 2
            ;;
        --no-compact)
            COMPACT=""
            shift
            ;;
        --limit|-n)
            LIMIT="--limit $2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE="--verbose"
            shift
            ;;
        --skip-download)
            SKIP_DOWNLOAD=true
            shift
            ;;
        --only)
            ONLY="$2"
            shift 2
            ;;
        --exclude)
            EXCLUDE="$2"
            shift 2
            ;;
        --stock)
            STOCK="$2"
            shift 2
            ;;
        --full)
            FULL_OUTPUT=true
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --host HOST         服务端地址 (默认: localhost)"
            echo "  --port PORT         服务端端口 (默认: 18812)"
            echo "  --format, -f FMT    输出格式: json/text/csv (默认: json)"
            echo "  --no-compact        不使用紧凑模式"
            echo "  --limit, -n N       限制输出条数"
            echo "  --verbose, -v       显示详细日志"
            echo "  --skip-download     跳过数据下载步骤"
            echo "  --only LEVEL        只运行指定级别: basic/daily/minute/financial/tick"
            echo "  --exclude LEVEL     排除指定级别"
            echo "  --stock CODE        测试股票代码 (默认: 000001.SZ)"
            echo "  --full              显示完整输出（不截断）"
            echo "  --help, -h          显示帮助"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# ==================== 构建命令前缀 ====================
CMD="xtdata --host $HOST --port $PORT -f $FORMAT $COMPACT $VERBOSE $LIMIT"

# 辅助函数：检查是否应该运行某个级别
should_run() {
    local level=$1
    if [[ -n "$ONLY" && "$ONLY" != "$level" ]]; then
        return 1
    fi
    if [[ -n "$EXCLUDE" && "$EXCLUDE" == "$level" ]]; then
        return 1
    fi
    return 0
}

# 辅助函数：截断输出
truncate_output() {
    if [[ "$FULL_OUTPUT" == true ]]; then
        cat
    elif [[ "$FORMAT" == "json" ]]; then
        head -c 300 && echo "..."
    else
        head -n 10
    fi
}

echo "=========================================="
echo "xtdata CLI 测试 (标准级别)"
echo "=========================================="
echo "配置:"
echo "  服务端: $HOST:$PORT"
echo "  格式: $FORMAT"
echo "  紧凑: $([ -n "$COMPACT" ] && echo "是" || echo "否")"
echo "  股票: $STOCK, $STOCK2"
[ -n "$ONLY" ] && echo "  仅运行: $ONLY"
[ -n "$EXCLUDE" ] && echo "  排除: $EXCLUDE"
echo "=========================================="

# ==================== 数据下载 ====================
if [[ "$SKIP_DOWNLOAD" != true ]] && should_run "download"; then
    echo ""
    echo "--- 数据下载 ---"

    echo "[1] download_history_data($STOCK, 1d, 20250101-20260309)"
    $CMD download_history_data --stock-code "$STOCK" --period "1d" --start-time "20250101" --end-time "20260309"
    echo ""

    echo "[2] download_history_data2([$STOCK,$STOCK2], 1d, 20250101-20260309)"
    $CMD download_history_data2 --stock-list "[\"$STOCK\",\"$STOCK2\"]" --period "1d" --start-time "20250101" --end-time "20260309"
    echo ""

    echo "[2.1] download_financial_data2([$STOCK], [Balance,Income,CashFlow])"
    $CMD download_financial_data2 --stock-list "[\"$STOCK\"]" --table-list "[\"Balance\",\"Income\",\"CashFlow\"]"
    echo ""
fi

# ==================== BASIC 级别 ====================
if should_run "basic"; then
    echo ""
    echo "--- BASIC 级别 ---"

    echo "[3] get_sector_list()"
    $CMD get_sector_list | truncate_output
    echo ""

    echo "[4] get_stock_list_in_sector(沪深A股)"
    $CMD get_stock_list_in_sector --sector-name "沪深A股" | truncate_output
    echo ""

    echo "[5] get_instrument_detail($STOCK)"
    $CMD get_instrument_detail --stock-code "$STOCK"
    echo ""

    echo "[6] get_divid_factors($STOCK, 20240101-20260101)"
    $CMD get_divid_factors --stock-code "$STOCK" --start-time "20240101" --end-time "20260101" | truncate_output
    echo ""
fi

# ==================== DAILY 级别 ====================
if should_run "daily"; then
    echo ""
    echo "--- DAILY 级别 (日线) ---"

    echo "[7] get_market_data([$STOCK,$STOCK2,$STOCK3,$STOCK4], 1d, 20260101-20260309)"
    $CMD get_market_data --stock-list "[\"$STOCK\",\"$STOCK2\",\"$STOCK3\",\"$STOCK4\"]" --period "1d" --start-time "20260101" --end-time "20260309" | truncate_output
    echo ""

    echo "[8] get_market_data_ex([$STOCK], 1d, 20260101-20260309)"
    $CMD get_market_data_ex --stock-list "[\"$STOCK\"]" --period "1d" --start-time "20260101" --end-time "20260309" | truncate_output
    echo ""

    echo "[8.1] get_market_data_ex([$STOCK,$STOCK2,$STOCK3,$STOCK4], 1d)"
    $CMD get_market_data_ex --stock-list "[\"$STOCK\",\"$STOCK2\",\"$STOCK3\",\"$STOCK4\"]" --period "1d" --start-time "20260101" --end-time "20260309" | truncate_output
    echo ""

    # echo "[9] get_full_kline([$STOCK], 1d, 20260201-20260228)"
    # $CMD get_full_kline --stock-list "[\"$STOCK\"]" --period "1d" --start-time "20260201" --end-time "20260228" | truncate_output
    # echo ""
fi

# ==================== MINUTE 级别 ====================
if should_run "minute"; then
    echo ""
    echo "--- MINUTE 级别 (分钟线) ---"

    echo "[10] get_market_data([$STOCK], 5m, 20260301-20260309)"
    $CMD get_market_data --stock-list "[\"$STOCK\"]" --period "5m" --start-time "20260301" --end-time "20260309" | truncate_output
    echo ""

    echo "[11] get_market_data_ex([$STOCK], 5m, 20260301-20260309)"
    $CMD get_market_data_ex --stock-list "[\"$STOCK\"]" --period "5m" --start-time "20260301" --end-time "20260309" | truncate_output
    echo ""
fi

# ==================== 财务数据 ====================
if should_run "financial"; then
    echo ""
    echo "--- 财务数据 ---"

    echo "[12] get_financial_data([$STOCK], [Balance,Income])"
    $CMD get_financial_data --stock-list "[\"$STOCK\"]" --table-list "[\"Balance\",\"Income\"]" | truncate_output
    echo ""
fi

# ==================== TICK 级别 ====================
if should_run "tick"; then
    echo ""
    echo "--- TICK 级别 ---"

    echo "[13] get_full_tick([$STOCK,$STOCK2])"
    $CMD get_full_tick --code-list "[\"$STOCK\",\"$STOCK2\"]"
    echo ""

    echo "[13.1] get_full_tick([$STOCK,$STOCK2,$STOCK3,$STOCK4])"
    $CMD get_full_tick --code-list "[\"$STOCK\",\"$STOCK2\",\"$STOCK3\",\"$STOCK4\"]"
    echo ""
fi

# ==================== 复权模式 ====================
if should_run "daily"; then
    echo ""
    echo "--- 复权模式 ---"

    echo "[14] get_market_data_ex([$STOCK], 1d, dividend=front)"
    $CMD get_market_data_ex --stock-list "[\"$STOCK\"]" --period "1d" --start-time "20260101" --end-time "20260309" --dividend-type "front" | truncate_output
    echo ""
fi

# ==================== count 参数 ====================
if should_run "daily"; then
    echo ""
    echo "--- count 参数 ---"

    echo "[15] get_market_data_ex([$STOCK], 1d, count=10)"
    $CMD get_market_data_ex --stock-list "[\"$STOCK\"]" --period "1d" --count 10 | truncate_output
    echo ""
fi

echo ""
echo "=========================================="
echo "测试完成!"
echo "=========================================="
