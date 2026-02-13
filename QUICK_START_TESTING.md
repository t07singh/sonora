# 🚀 Quick Start: Sonora Full Integration & Performance Testing

## Overview

This guide walks you through running the complete Sonora integration and performance test suite, including GPU/CPU monitoring, visualizations, and Streamlit dashboard integration.

---

## 📋 Prerequisites

1. **Start the Sonora API Server:**
   ```bash
   cd sonora
   python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
   ```

2. **Install Additional Dependencies:**
   ```bash
   pip install psutil plotly matplotlib pillow pandas
   ```

---

## 🧪 Quick Test Commands

### Option 1: Run Everything (Recommended)

```bash
# Run full test suite (tests + benchmark + report)
python sonora/scripts/run_full_test_suite.py
```

This will:
- ✅ Run all integration tests
- ✅ Run performance benchmark with system monitoring
- ✅ Generate performance report
- ✅ Create visualizations
- ✅ Log everything to `/logs/test_results.log`

### Option 2: Run Individual Components

#### Run Integration Tests Only
```bash
python sonora/scripts/run_tests.py
```

#### Run Performance Benchmark Only
```bash
python sonora/scripts/benchmark_system_performance.py
```

#### Generate Report Only
```bash
python sonora/scripts/generate_performance_report.py
```

---

## 📊 View Results

### 1. Check Generated Reports

All reports are saved to `/reports/` directory:

- `performance_summary.md` - Comprehensive performance summary
- `system_metrics.json` - Detailed metrics in JSON
- `system_metrics.csv` - Metrics in CSV format
- `latency_histogram.png` - Latency distribution chart
- `gpu_usage.html` - GPU memory usage chart
- `memory_timeline.html` - Memory usage over time
- `quality_correlation.html` - Quality correlation chart

### 2. View in Streamlit Dashboard

```bash
# Start Streamlit UI
streamlit run ui/app.py
```

Then navigate to:
- **Performance Dashboard** section (scroll down)
- View charts in tabs:
  - **Latency & Throughput** - Latency metrics and charts
  - **Resource Usage** - CPU/GPU/Memory usage
  - **Quality Metrics** - Quality correlation and scores
  - **Error Logs** - Test logs and error statistics

### 3. Check Logs

```bash
# View test logs
cat logs/test_results.log

# Or view in real-time
tail -f logs/test_results.log
```

---

## 🎯 Expected Results

### Test Status

| Test | Expected Result |
|------|----------------|
| API Health | ✅ Status: "ok", all components initialized |
| Translation | ✅ Latency < 6s (cold), < 1s (warm) |
| Coqui TTS | ✅ Latency < 4s, playable audio |
| VibeVoice | ✅ Latency < 3s, quality audio |
| Emotion Detection | ✅ Emotion detected, confidence > 0.5 |
| End-to-End Dubbing | ✅ Full pipeline completes |

### Performance Metrics

- **Average Latency:** < 3 seconds
- **CPU Usage:** < 80%
- **Memory Usage:** < 85%
- **Success Rate:** > 90%

---

## 🔧 Troubleshooting

### API Not Responding

```bash
# Check if server is running
curl http://127.0.0.1:8000/health

# Check port
netstat -ano | findstr ":8000"
```

### Missing Dependencies

```bash
pip install psutil plotly matplotlib pillow pandas
```

### No GPU Data

If GPU monitoring shows "No GPU data available":
- Ensure CUDA is installed (if using GPU)
- Check `torch.cuda.is_available()` returns `True`
- GPU monitoring will gracefully fall back to CPU-only metrics

### Visualization Errors

If charts don't appear:
- Check that `plotly` and `matplotlib` are installed
- Verify files exist in `/reports/` directory
- Check browser console for errors

---

## 📈 Understanding the Metrics

### Latency Metrics

- **Total Latency:** Time from request to response
- **Processing Time:** Actual model inference time
- **Network Overhead:** Difference between total and processing time

### Resource Usage

- **CPU Percent:** Average CPU usage during benchmark
- **Memory Percent:** Average RAM usage
- **GPU Memory:** GPU memory allocated (if GPU available)

### Quality Metrics

- **Efficiency Score:** Overall system performance (0-100)
- **Success Rate:** Percentage of successful tests
- **Per-Endpoint Stats:** Individual endpoint performance

---

## 🚀 Next Steps

1. **Review Performance Summary:** Check `/reports/performance_summary.md`
2. **Optimize Slow Endpoints:** Review recommendations in the report
3. **Monitor in Dashboard:** Use Streamlit UI for real-time monitoring
4. **Run Regular Benchmarks:** Schedule periodic benchmarks to track performance

---

## 📝 Notes

- All tests run **offline** (no external API calls)
- Benchmark duration: ~5-10 minutes depending on system
- Test audio files are optional (set via environment variables)
- Logs are automatically saved to `/logs/test_results.log`

---

**For detailed documentation, see:**
- `sonora/TEST_PLAN.md` - Complete test plan
- `sonora/TEST_SUITE_SUMMARY.md` - Test suite overview

---

**Version:** 1.0.0  
**Last Updated:** 2024













