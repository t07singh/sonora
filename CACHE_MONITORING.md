# 🧠 Sonora Cache Monitoring System

Real-time cache performance monitoring and management for the Sonora AI Dubbing System.

## 🎯 Features

- **Real-time Statistics**: Live cache performance metrics
- **Memory & Disk Monitoring**: Track both in-memory and disk cache usage
- **Hit Rate Analytics**: Monitor cache effectiveness
- **Manual Cache Management**: Clear cache with one click
- **Performance Trends**: Historical performance charts
- **REST API Endpoints**: Programmatic access to cache data

## 🚀 Quick Start

### 1. Start the API Server

```bash
# Start the FastAPI server
python -m sonora.api.server

# Or with uvicorn
uvicorn sonora.api.server:app --reload
```

The server will be available at `http://localhost:8000`

### 2. Launch the Dashboard

```bash
# Start the Streamlit dashboard
python -m sonora.run_cache_dashboard
```

The dashboard will be available at `http://localhost:8501`

### 3. Test the System

```bash
# Run the test script
python -m sonora.test_cache_monitoring
```

## 📊 API Endpoints

### GET `/api/cache/stats`

Returns comprehensive cache statistics:

```json
{
  "memory_items": 15,
  "disk_items": 8,
  "hit_rate": 0.75,
  "expired_entries": 3,
  "uptime_minutes": 45.2,
  "cache_size_mb": 2.3,
  "total_requests": 100,
  "memory_hits": 60,
  "disk_hits": 15,
  "misses": 25,
  "max_memory_size": 200,
  "default_ttl": 3600,
  "cache_dir": "/path/to/cache",
  "timestamp": 1703123456.789
}
```

### DELETE `/api/cache/clear`

Clears all cache entries:

```json
{
  "status": "Cache cleared successfully",
  "cleared_items": {
    "memory_items": 15,
    "disk_items": 8,
    "total_items": 23
  },
  "timestamp": 1703123456.789
}
```

## 🎛️ Dashboard Features

### Real-time Metrics
- **Memory Items**: Number of items in memory cache
- **Disk Items**: Number of items in disk cache  
- **Hit Rate**: Cache effectiveness percentage
- **Cache Size**: Total cache size in MB

### Performance Charts
- **Cache Items Over Time**: Memory vs disk usage trends
- **Hit Rate Over Time**: Performance trends
- **Cache Size Over Time**: Storage usage trends

### Manual Controls
- **Auto-refresh**: Automatic updates every 30 seconds
- **Manual Refresh**: Force immediate update
- **Clear Cache**: Remove all cached data
- **Raw Data View**: JSON data inspection

## 🧪 Testing

### Run All Tests

```bash
# Run comprehensive test suite
pytest tests/test_cache_monitoring.py -v
```

### Test Categories

- **Cache Manager Stats**: Statistics tracking and accuracy
- **API Endpoints**: REST API functionality
- **Integration Tests**: End-to-end workflows
- **Performance Tests**: Load and concurrent access
- **Edge Cases**: Error conditions and limits

### Quick Validation

```bash
# Run quick validation script
python -m sonora.test_cache_monitoring
```

## 🔧 Configuration

### Cache Manager Settings

```python
from sonora.utils.cache_manager import CacheManager

cache_manager = CacheManager(
    cache_dir="cache",           # Disk cache directory
    max_memory_size=200,         # Max memory items
    default_ttl=3600            # Default TTL in seconds
)
```

### Dashboard Configuration

Edit `sonora/ui/cache_dashboard.py`:

```python
# API Configuration
API_BASE_URL = "http://localhost:8000"  # Change if needed
```

## 📈 Monitoring Best Practices

### Key Metrics to Watch

1. **Hit Rate**: Should be > 70% for good performance
2. **Memory Usage**: Monitor for memory pressure
3. **Disk Usage**: Watch for disk space
4. **Expired Entries**: High numbers may indicate TTL issues

### Performance Optimization

1. **Adjust TTL**: Balance freshness vs performance
2. **Memory Size**: Increase for better hit rates
3. **Cleanup Frequency**: Monitor expired entry cleanup
4. **Cache Keys**: Use consistent, efficient key patterns

## 🐛 Troubleshooting

### Common Issues

**Dashboard shows "API Disconnected"**
- Ensure FastAPI server is running on port 8000
- Check firewall/network settings
- Verify API_BASE_URL in dashboard config

**Cache stats show 0 items**
- Check cache directory permissions
- Verify cache manager initialization
- Look for error logs

**High memory usage**
- Reduce max_memory_size
- Decrease default_ttl
- Monitor for memory leaks

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 Security Considerations

- **API Access**: Consider authentication for production
- **Cache Data**: Sensitive data may be cached
- **Network**: Use HTTPS in production
- **Permissions**: Secure cache directory access

## 📚 Architecture

### Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Cache Manager  │    │   Streamlit     │
│   Server        │◄──►│                  │◄──►│   Dashboard     │
│                 │    │  - Memory Cache  │    │                 │
│ /api/cache/stats│    │  - Disk Cache    │    │ - Real-time UI  │
│ /api/cache/clear│    │  - Statistics    │    │ - Charts        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow

1. **Cache Operations**: Components use cache manager
2. **Statistics Collection**: Manager tracks all operations
3. **API Endpoints**: FastAPI exposes statistics
4. **Dashboard**: Streamlit visualizes data
5. **Manual Controls**: Dashboard can clear cache

## 🚀 Production Deployment

### Docker Support

```dockerfile
# Add to your Dockerfile
COPY sonora/ /app/sonora/
RUN pip install streamlit plotly
```

### Environment Variables

```bash
# Cache configuration
CACHE_DIR=/app/cache
MAX_MEMORY_SIZE=500
DEFAULT_TTL=7200

# API configuration  
API_HOST=0.0.0.0
API_PORT=8000
DASHBOARD_PORT=8501
```

### Monitoring Integration

- **Prometheus**: Export metrics via `/api/cache/stats`
- **Grafana**: Create dashboards from API data
- **Logging**: Structured logs for analysis
- **Alerts**: Set up hit rate and size alerts

## 📝 License

Part of the Sonora AI Dubbing System. See main project license.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review test cases for examples
- Open an issue on GitHub
- Check the main Sonora documentation










