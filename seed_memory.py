import asyncio
import uuid
from vanna_setup import get_agent
from vanna.core.tool import ToolContext
from vanna.core.user.models import User

# 15 training pairs (same as before)
training_pairs = [
    ("How many patients do we have?", "SELECT COUNT(*) AS total_patients FROM patients"),
    ("List all patients from New York", "SELECT first_name, last_name, city FROM patients WHERE city = 'New York'"),
    ("Show me female patients", "SELECT first_name, last_name, gender FROM patients WHERE gender = 'F'"),
    ("List all doctors and their specializations", "SELECT name, specialization FROM doctors"),
    ("Which doctor has the most appointments?",
     "SELECT d.name, COUNT(a.id) as appointment_count FROM doctors d JOIN appointments a ON d.id = a.doctor_id GROUP BY d.id ORDER BY appointment_count DESC LIMIT 1"),
    ("Show me cancelled appointments", "SELECT * FROM appointments WHERE status = 'Cancelled'"),
    ("How many appointments were completed last month?",
     "SELECT COUNT(*) FROM appointments WHERE status = 'Completed' AND strftime('%Y-%m', appointment_date) = strftime('%Y-%m', 'now', '-1 month')"),
    ("What is the total revenue?", "SELECT SUM(total_amount) AS total_revenue FROM invoices WHERE status = 'Paid'"),
    ("Show revenue by doctor",
     "SELECT d.name, SUM(i.total_amount) AS total_revenue FROM invoices i JOIN appointments a ON a.patient_id = i.patient_id JOIN doctors d ON d.id = a.doctor_id WHERE i.status = 'Paid' GROUP BY d.name ORDER BY total_revenue DESC"),
    ("What is the average treatment cost?", "SELECT AVG(cost) AS average_treatment_cost FROM treatments"),
    ("Show unpaid invoices", "SELECT * FROM invoices WHERE status = 'Pending' OR status = 'Overdue'"),
    ("Show monthly appointment trend",
     "SELECT strftime('%Y-%m', appointment_date) as month, COUNT(*) as appointment_count FROM appointments GROUP BY month ORDER BY month DESC"),
    ("How many patients registered in the last 3 months?",
     "SELECT COUNT(*) FROM patients WHERE registered_date >= date('now', '-3 months')"),
    ("Which city has the most patients?",
     "SELECT city, COUNT(*) as patient_count FROM patients GROUP BY city ORDER BY patient_count DESC LIMIT 1"),
    ("Top 5 patients by spending",
     "SELECT p.first_name, p.last_name, SUM(i.total_amount) as total_spending FROM patients p JOIN invoices i ON p.id = i.patient_id WHERE i.status = 'Paid' GROUP BY p.id ORDER BY total_spending DESC LIMIT 5"),
]

async def seed_memory():
    print("="*50)
    print("SEEDING AGENT MEMORY")
    print("="*50)
    try:
        agent = get_agent()
        print("✓ Agent loaded successfully")

        # Create a User object that matches your SimpleUserResolver
        user = User(
            id="default_user",
            email="user@example.com",
            group_memberships=["user"]
        )

        for i, (question, sql) in enumerate(training_pairs, 1):
            # Build a complete ToolContext with all required fields
            context = ToolContext(
                user=user,
                conversation_id=str(uuid.uuid4()),   # unique per interaction
                request_id=str(uuid.uuid4()),        # unique per request
                agent_memory=agent.agent_memory      # pass the agent's memory
            )
            # Save the successful tool usage (this seeds the memory)
            await agent.agent_memory.save_tool_usage(
                question=question,
                tool_name="RunSqlTool",
                args={"sql": sql},
                context=context,
                success=True
            )
            print(f"  {i}. Seeded: {question[:50]}...")

        print(f"\n✓ Successfully seeded {len(training_pairs)} Q&A pairs")
        print("Memory seeding completed without validation errors.")

    except Exception as e:
        print(f"✗ Error seeding memory: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(seed_memory())