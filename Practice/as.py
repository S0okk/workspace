import asyncio
import random

async def randomize():
    await asyncio.sleep(0.01)
    return random.randint(1, 100)

async def main():
    tasks = [randomize() for i in range(10)]
    nums = await asyncio.gather(*tasks)
    
    avg = sum(nums) / len(nums)
    
    print(nums)
    print(f"avg: {avg}")





if __name__ == "__main__":
    asyncio.run(main())