import os
import pandas as pd
import json
import requests
from time import sleep
from dotenv import load_dotenv
from typing import Dict, Any
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def parse_model_response(content: str) -> Dict[str, Any]:
    """
    모델의 응답이 코드 블록(```json ... ```) 형태일 경우 이를 제거하고 JSON 파싱을 수행합니다.
    """
    # 응답 내용이 코드 블록으로 감싸져 있다면 제거
    if content.startswith("```"):
        lines = content.splitlines()
        # 첫번째 줄이 ``` 또는 ```json 인 경우 제거
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        # 마지막 줄이 ``` 인 경우 제거
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines)
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print("JSON parsing error:", e)
        print("Content received:", content)
        return {"score": None, "reason": "JSON parsing error"}

# Create an instance of the OpenAI client (adjust this according to your library)
from openai import OpenAI  # Adjust import if needed

client = OpenAI(api_key=OPENAI_API_KEY)

BRANDS = ['lyft', 'redbull', 'kroger', 'sephora', 'nestle', 'lululemon']
INPUT_CSV_FILE = 'top_influencer_corpus.csv'
OUTPUT_CSV_FILE = 'ad_suitability_results.csv'

criteria = {
    "lululemon":"""- Brand Alignment & Lifestyle: Influencers should embody an active, mindful, and balanced lifestyle that aligns with lululemon’s core values of wellness, yoga, and community engagement.
- Authenticity & Credibility: The influencer’s content must appear genuine and relatable, with a clear focus on health, fitness, and personal growth, ensuring they truly live the lifestyle they promote.
- High-Quality Aesthetics: Visual and content quality should reflect lululemon’s premium brand image, emphasizing clean, modern, and inspiring visuals.
- Community Engagement: Prioritize influencers with highly engaged, loyal audiences who participate in conversations around wellness, sustainability, and active living.
- Ethical & Sustainable Practices: Influencers should demonstrate a commitment to ethical practices and sustainability, aligning with lululemon’s emphasis on responsible living.""",
    
    "kroger":"""- Brand Alignment & Everyday Living: Influencers should embody reliability and approachability, resonating with Kroger’s commitment to quality, affordability, and convenience for everyday family life.
- Authenticity & Community Connection: Content must be genuine and relatable, reflecting local community values and a strong connection to family and neighborhood life.
- Culinary Expertise & Health Focus: Influencers should emphasize healthy eating, cooking tips, and food quality, aligning with Kroger’s focus on fresh produce and nutritional well-being.
- Diversity & Inclusivity: The influencer must appeal to a diverse customer base, representing various lifestyles and cultural backgrounds in an authentic manner.
- Sustainability & Local Sourcing: A commitment to sustainability, local sourcing, and eco-friendly practices is key, ensuring that the influencer’s message aligns with Kroger’s initiatives in environmental responsibility.
""",
    
    "lyft": """- Urban Mobility & Connectivity: Influencers should embody a modern, tech-savvy lifestyle that reflects Lyft’s commitment to innovative and accessible urban transportation.
- Reliability & Trustworthiness: Content must emphasize safety, dependability, and ease of use, mirroring Lyft’s reputation for reliable ride-sharing services.
- Inclusivity & Community Focus: Influencers should appeal to a diverse urban audience, fostering a sense of community and inclusivity that resonates with Lyft’s user base.
- Sustainability & Social Impact: Prioritize influencers who highlight eco-friendly transportation options and community-driven initiatives, aligning with Lyft’s commitment to reducing environmental impact.
- Engagement & Storytelling: Influencers must be adept at sharing engaging, authentic narratives that connect everyday experiences with the convenience and innovation of Lyft’s services.
""",
    
    "nestle":"""- Brand Alignment & Diverse Portfolio: Influencers should reflect the wide range of Nestle products—from beverages to nutritional foods—while appealing to a global audience.
- Authenticity & Trustworthiness: Content must be genuine and resonate with values of quality, safety, and nutritional excellence that consumers associate with Nestle.
- Health & Nutrition Focus: Influencers should emphasize balanced diets and healthy lifestyles, aligning with Nestle’s commitment to nutrition and wellness.
- Sustainability & Ethical Practices: It is essential that influencers demonstrate a commitment to sustainability, ethical sourcing, and environmental responsibility.
- Community Engagement & Inclusivity: Prioritize influencers who build strong, engaged communities across diverse demographics, promoting inclusivity and consumer well-being.
""",
    
    "redbull":"""- Brand Alignment & Extreme Lifestyle: Influencers should embody a bold, adventurous lifestyle that aligns with Redbull’s core identity of extreme sports, high-energy activities, and pushing boundaries.
- Authenticity & Energy: The influencer’s content must radiate genuine enthusiasm and a passion for adrenaline-fueled pursuits, resonating with Redbull’s energetic brand ethos.
- Dynamic Visual Storytelling: Content should be visually compelling and dynamic, capturing thrilling moments and high-impact visuals that reflect the brand’s spirit of adventure.
- Community Engagement: Prioritize influencers who actively engage with communities interested in extreme sports, innovation, and adventurous lifestyles, fostering an interactive and loyal fanbase.
- Innovation & Trendsetting: Influencers should be recognized for their creativity and willingness to experiment, positioning themselves as trendsetters within the realms of sports, music, and culture.
""",
    
    "sephora":"""- Beauty Expertise & Trendsetting: Influencers should have a strong passion for beauty, skincare, and cosmetics, consistently staying ahead of trends and experimenting with new looks.
- Authenticity & Inclusivity: Content must be genuine and diverse, appealing to a wide audience by showcasing a range of skin tones, ages, and styles that align with Sephora’s inclusive brand ethos.
- High-Quality Visual Content: The influencer’s imagery should be polished and visually compelling, reflecting Sephora’s premium, high-fashion aesthetic.
- Engagement & Community Building: Prioritize influencers who actively engage with their audience through tutorials, reviews, and interactive content that fosters a community centered around beauty innovation.
- Innovation & Product Knowledge: Influencers should demonstrate deep product knowledge and a willingness to experiment with new beauty trends, positioning themselves as trusted advisors in the beauty space.
"""
}

def evaluate_influencer_for_brand(influencer_name: str,
                                  wikipedia_corpus: str,
                                  updates_corpus: str,
                                  brand_name: str,
                                  brand_criteria: str) -> Dict[str, Any]:
    system_prompt = (
        "You are an AI agent specialized in determining advertising suitability. "
        "You have in-depth knowledge of influencer marketing and brand advertising criteria. "
        "Given details about an influencer and a brand, you must evaluate how suitable the influencer is for advertising that brand. "
        "Your response must be strictly formatted as JSON with exactly two keys: 'score' and 'reason'."
    )

    user_prompt = f"""
Influencer Information:
Name of Influencer: {influencer_name}
Wikipedia of Influencer: {wikipedia_corpus}
Other Updates of Influencer: {updates_corpus}
---
Brand Information:
Brand Name: {brand_name}
Brand Criteria for Ad Model: {brand_criteria}
---
Instructions:
1. Assess the influencer's overall suitability for the brand based on the information provided.
2. Provide a "score" between 0.000 and 1.000 (inclusive), formatted as a float with exactly three decimal places. 
   A score of 1.000 indicates exceptional suitability, while 0.000 indicates unsuitability.
3. Provide a brief explanation (one or two sentences) as "reason", highlighting key points that influenced your evaluation.
4. Output your response strictly as a JSON object, exactly in the following format:
   {{
       "score": 0.XXX,
       "reason": "Your brief explanation here."
   }}
5. Do not include any additional text, commentary, or formatting outside of the JSON object.
    """

    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 모델 이름이 올바른지 확인하세요.
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.0  # 결정론적 출력을 위해 설정
        )
        content = response.choices[0].message.content
        print(content)
        result = parse_model_response(content)
        return result
    except Exception as e:
        print(f"Error processing influencer {influencer_name} for brand {brand_name}: {e}")
        return {"score": None, "reason": "Error during evaluation"}

def main():
    # pandas를 사용하여 CSV 읽기
    df = pd.read_csv(INPUT_CSV_FILE)
    
    # 결과를 저장할 리스트 초기화
    results = []
    
    # 각 인플루언서와 브랜드에 대해 평가 진행
    for idx, row in df.iterrows():
        influencer = row['influencer']
        wikipedia_corpus = row['wikipedia_corpus']
        updates_corpus = row['updates_corpus']
        
        for brand in BRANDS:
            print(f"Evaluating {influencer} for {brand}...")
            brand_criteria = criteria.get(brand, "")
            evaluation = evaluate_influencer_for_brand(
                influencer,
                wikipedia_corpus,
                updates_corpus,
                brand,
                brand_criteria
            )
            results.append({
                "brand": brand,
                "influencer": influencer,
                "score": evaluation.get("score"),
                "reason": evaluation.get("reason")
            })
            
            # 속도 제한을 위해 잠시 대기
            sleep(1)
    
    # 결과 리스트를 pandas DataFrame으로 변환
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8')
    print(f"Results saved to {OUTPUT_CSV_FILE}")

if __name__ == "__main__":
    main()