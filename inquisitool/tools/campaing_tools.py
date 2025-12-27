from crewai import Task

from inquisitool.db.mongodb import get_campaign


class QuestionCounterTool:
    def __init__(self):
        """Initialize the QuestionCounter tool"""
        pass

    async def count_campaign_questions(self, campaign_id: str) -> int:
        """
        Count number of questions for a specific campaign
        """
        try:
            campaign = await get_campaign(campaign_id)
            return campaign.get("number_of_questions", 0)
        except Exception as e:
            print(f"Database error: {e}")
            return 0

    async def execute(self, campaign_id: str) -> dict:
        """
        Execute the question counting task
        """
        question_count = await self.count_campaign_questions(campaign_id)

        return {"campaign_id": campaign_id, "total_questions": question_count}


# Example Task using the tool
def create_counter_task(campaign_id: str) -> Task:
    counter_tool = QuestionCounterTool()

    return Task(
        description=f"Count total questions for campaign {campaign_id}",
        tools=counter_tool,
        expected_output="Dictionary with campaign ID and total question count",
    )
