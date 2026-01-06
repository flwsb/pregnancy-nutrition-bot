# OpenAI Model Selection Guide

## Current Model Choices (Optimized for Cost & Performance)

### Image Analysis (Vision)
**Model: `gpt-4o`**

- **Why**: GPT-4o is OpenAI's flagship multimodal model with excellent vision capabilities, specifically designed for image understanding tasks
- **Performance**: High accuracy for complex meal photo analysis, identifying multiple foods and estimating portions
- **Cost**: ~$2.50-$5.00 per million input tokens (images are tokenized)
- **Alternative**: `gpt-4o-mini` - Cheaper (~$0.60/$2.40 per million tokens) but may have lower accuracy for complex meals

**Note**: GPT-5.2 models (as of 2026) may not support vision/image inputs. GPT-4o remains the best choice for vision tasks.

### Text Recommendations
**Model: `gpt-4o-mini`**

- **Why**: Most cost-effective option for text generation tasks
- **Performance**: Excellent for generating personalized nutrition recommendations
- **Cost**: $0.15 per million input tokens, $0.60 per million output tokens
- **Alternative Options**:
  - `gpt-5.1-mini`: $0.20/$1.60 per million tokens - Newer than 4o-mini, but 2.7x more expensive for output
  - `gpt-5.2-mini`: $0.25/$2.00 per million tokens - Latest mini model, but 3.3x more expensive for output
  - `gpt-5.2-thinking`: $1.75/$14.00 per million tokens - Better for complex reasoning, but 23x more expensive

## Cost Comparison (Approximate)

### Per 1,000 Image Analyses (Vision)
- **GPT-4o**: ~$2.50-$5.00 (recommended)
- **GPT-4o-mini**: ~$0.60-$1.20 (if accuracy is acceptable)

### Per 1,000 Recommendation Generations (Text)
- **GPT-4o-mini**: ~$0.60 (recommended - CHEAPEST)
- **GPT-5.1-mini**: ~$1.60 (2.7x more expensive)
- **GPT-5.2-mini**: ~$2.00 (3.3x more expensive)
- **GPT-5.2-thinking**: ~$14.00 (23x more expensive)

## Model Selection Rationale

1. **Vision Task**: Requires high accuracy to identify foods correctly - GPT-4o is worth the extra cost
2. **Text Task**: Simple recommendation generation - GPT-4o-mini provides excellent value
3. **Overall**: This combination provides the best balance of accuracy and cost efficiency

## How to Change Models

Edit `openai_service.py`:

1. **For Vision Analysis** (line ~31):
   ```python
   model="gpt-4o"  # Change to "gpt-4o-mini" for cheaper option
   ```

2. **For Recommendations** (line ~163):
   ```python
   model="gpt-4o-mini"  # Change to "gpt-5.1-mini", "gpt-5.2-mini", or "gpt-5.2-thinking" for better reasoning
   ```

## Future Considerations

- Monitor OpenAI's model updates - if GPT-5.2 or newer models add vision support, they may become better options
- If you need higher accuracy for recommendations, consider `gpt-5.2-thinking` despite higher cost
- For very high volume usage, consider `gpt-4o-mini` for vision if accuracy is acceptable

