import json

from openai import OpenAI


def generate_business_analysis(business_data):
    """
    Analyse Smart Bus business data using a local Ollama model.
    """

    prompt = f"""
You are an AI Business Analysis Assistant for a
Smart Bus Management System in Malaysia.

Analyse the following business data:

{json.dumps(business_data, indent=2, default=str)}

Your task is to identify meaningful:

- Business opportunities
- Business risks
- Operational problems
- Cost issues
- Demand patterns
- Growth opportunities
- Fleet issues
- Driver performance based on customer star ratings
- Customer satisfaction with drivers
- Drivers receiving consistently high or low ratings
- Drivers requiring performance improvement
- Customer behaviour
- Revenue patterns
- Maintenance issues
- Fuel efficiency issues

Do not simply repeat the numbers.

Look for relationships between different data points.

For example:
- Compare booking demand with available vehicle capacity.
- Compare revenue changes with booking changes.
- Compare maintenance cost with vehicle usage.
- Compare drivers using average customer star ratings.
- Consider the total number of customer reviews for each driver.
- Identify drivers with high customer satisfaction.
- Identify drivers with low customer satisfaction.
- Identify drivers who have not received customer ratings.
- Compare drivers only when sufficient rating evidence exists.
- Identify routes with unusually high or low demand.
- Identify operational areas that may require management attention.

Generate recommendations dynamically based on the supplied data.

IMPORTANT RULES:

1. Only use the supplied business data.

2. Never invent facts, numbers, records, relationships,
   comparisons, ratings, distances, utilisation rates,
   capacity figures or trends.

3. Carefully distinguish between:
   - number of vehicles
   - number of available vehicles
   - seat capacity
   - number of bookings
   - passenger count

   Do NOT treat the number of available vehicles as vehicle
   capacity.

4. Fleet recommendations must consider actual seat capacity,
   passenger demand, booking volume and vehicle status when
   these values are available.

5. Do not recommend purchasing additional vehicles merely
   because there are bookings or because some vehicles are
   unavailable.

6. Only recommend additional vehicles when the supplied data
   provides clear evidence that existing capacity may be
   insufficient.

7. A single high-revenue month must NOT automatically be
   described as a peak season.

8. Only describe revenue as a trend when multiple historical
   periods are available and the direction is supported by
   those periods.

9. When discussing revenue growth, distinguish between:
   - a change between two periods
   - a longer-term trend
   - a seasonal pattern

10. DRIVER PERFORMANCE ANALYSIS

    Driver performance must be evaluated primarily using
    customer star ratings from completed bookings.

    Use the following data when available:

    - average_rating
    - total_reviews
    - performance_category
    - overall_average_rating
    - total_customer_reviews

    Do not use completed trips or revenue as indicators
    of driver service quality.

11. DRIVER PERFORMANCE CLASSIFICATION

    Use the supplied performance_category, based on:

    4.50 - 5.00 = Excellent
    4.00 - 4.49 = Good
    3.00 - 3.99 = Satisfactory
    2.00 - 2.99 = Needs Improvement
    1.00 - 1.99 = Poor

    If average_rating is null or total_reviews is zero,
    the driver must be classified as "Not Yet Rated".

    Never interpret missing ratings as poor performance.

    Do not describe a driver as the best or highest-rated
    unless a comparison with other rated drivers supports
    that statement.

12. DRIVER PERFORMANCE RECOMMENDATIONS

    Recommendations must be based on customer rating data.

    For Excellent drivers:
    - Consider recognising positive customer feedback.
    - Consider eligibility for performance rewards.
    - Do not automatically recommend rewards.

    For Good drivers:
    - Recommend maintaining service quality.
    - Identify opportunities for continued improvement.

    For Satisfactory drivers:
    - Consider reviewing customer feedback.
    - Identify areas for service improvement.

    For Needs Improvement drivers:
    - Recommend reviewing customer complaints.
    - Consider appropriate driver training.

    For Poor drivers:
    - Recommend investigating recurring service concerns.
    - Consider additional training and performance monitoring.

    For Not Yet Rated drivers:
    - State that insufficient customer rating data exists.
    - Recommend collecting customer feedback.

    Always consider the total number of reviews.

    A driver with one 5-star review must not automatically
    be considered more reliable than a driver with many
    consistently positive reviews.

    Do not invent customer comments or complaints.

    Do not describe a low rating as proof of misconduct.

    If there are no customer ratings, explicitly state
    that driver service quality cannot yet be assessed.

13. Maintenance cost alone does not establish that maintenance
    cost is high, excessive, inefficient or justified.

14. When analysing maintenance, consider maintenance records,
    cost and vehicle information together when available.

15. Do not describe fuel data as "fuel efficiency" unless the
    supplied data contains an appropriate efficiency measure,
    such as fuel consumption relative to distance travelled.

16. Fuel cost, total litres and average fuel price alone must
    not be described as fuel efficiency.

17. If the available data is insufficient to establish a
    conclusion, explicitly state that limitation rather than
    making an unsupported claim.

18. Recommendations must be based on relationships between
    available data whenever possible.

19. Do not automatically recommend buying vehicles.

20. Do not automatically recommend rewarding drivers.

21. Recommendations must be practical for a Malaysian bus
    charter and tourism transportation business.

22. Use cautious language such as:
    "consider", "review", "may indicate", "could", or
    "the available data suggests".

23. Avoid duplicate recommendations.

24. Prioritise findings with clear evidence and meaningful
    business relevance.

25. Use Malaysian English.

26. Keep recommendations concise.

27. Return ONLY valid JSON.

28. Return between 3 and 6 recommendations when sufficient
    evidence exists.

29. If fewer than 3 recommendations are properly supported,
    return fewer than 3. Do not create unsupported
    recommendations simply to reach the minimum.

30. DRIVER PERFORMANCE EVIDENCE

    When generating a Driver Performance Analysis:

    - Include the driver's name.
    - Include the actual average star rating.
    - Include the number of customer reviews.
    - Explain what the rating may indicate.
    - Provide a practical management recommendation.

    Do not use revenue or completed trips as evidence
    of customer satisfaction.

    Only generate a driver performance recommendation
    when relevant driver rating data exists.

    If all drivers are unrated, do not invent a driver
    performance comparison.

    Driver performance findings should use the
    category "Driver Performance".

For every recommendation:

- "finding" must describe only what the data demonstrates.
- "recommendation" must be a practical management action.
- "evidence" must identify the actual supplied data supporting
  the finding.

Each recommendation must clearly distinguish:

- What the data shows
- What management could consider
- What specific evidence supports the recommendation

Return between 3 and 6 recommendations when sufficient evidence exists.
If fewer than 3 recommendations are supported by the data, return fewer.
Never invent a recommendation just to reach 3.

Use exactly this structure:

[
    {{
        "category": "Fleet",
        "title": "Short descriptive title",
        "finding": "What the data shows.",
        "recommendation": "What management could consider doing.",
        "evidence": "The specific data or relationship supporting the recommendation."
    }}
]
"""

    try:

        client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )

        response = client.chat.completions.create(
            model="llama3.1",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a business analysis assistant. "
                        "Return only valid JSON when requested."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
        )

        response_text = response.choices[0].message.content.strip()

        # Remove markdown code fences if returned
        if response_text.startswith("```json"):
            response_text = response_text[7:]

        if response_text.startswith("```"):
            response_text = response_text[3:]

        if response_text.endswith("```"):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        result = json.loads(response_text)

        if not isinstance(result, list):
            print("AI Business Analysis did not return a list.")
            return []

        return result

    except json.JSONDecodeError as exc:

        print(
            f"AI Business Analysis returned invalid JSON: {exc}"
        )

        return []

    except Exception as exc:

        print(
            f"AI Business Analysis error: {exc}"
        )

        return []