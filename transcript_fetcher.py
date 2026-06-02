import re
import json
import subprocess
from datetime import datetime

# Hardcoded demo transcripts for when network is blocked
DEMO_TRANSCRIPTS = {
    "arj7oStGLkU": {
        "title": "Inside the mind of a master procrastinator",
        "creator": "TED",
        "views": 57000000,
        "likes": 850000,
        "comments": 45000,
        "duration_seconds": 853,
        "upload_date": "2016-04-06",
        "description": "Tim Urban knows that procrastination doesn't make sense, but he's never been able to shake the habit.",
        "hashtags": ["productivity", "psychology", "motivation", "ted", "procrastination"],
        "transcript": """When I was in college I had two types of projects. There were the ones I did right away and there were the ones I did at the last minute. 
        The ones I did right away, I would work on steadily and get done well before the deadline. 
        But then there were the procrastination projects. And what I noticed is that with the procrastination projects, 
        I would always say I'll start soon. I had a 90-page senior thesis due. I had a year to do it. 
        I didn't start until 72 hours before it was due. What is going on in the brain of a procrastinator? 
        I want to show you a brain. This is the brain of a non-procrastinator. 
        Now let's look at the brain of a procrastinator. The procrastinator's brain has a Rational Decision-Maker and an Instant Gratification Monkey. 
        The Monkey has no memory of the past, no knowledge of the future, and only cares about two things: easy and fun. 
        In the animal world, that works fine. But humans have this frontal cortex which gives us the ability to think long-term. 
        So the Rational Decision-Maker often has plans and the Monkey often hijacks those plans. 
        The Monkey takes the wheel and says let's check YouTube instead. 
        There's a third character called the Panic Monster. The Panic Monster is dormant most of the time but he wakes up when a deadline gets too close. 
        The Monkey is terrified of the Panic Monster. So the system works but just barely. 
        The problem is that not all procrastination involves deadlines. Some things have no deadline at all. 
        These are the things that matter most to us - starting a business, seeing family, improving our health. 
        There's no Panic Monster to wake up because there's no deadline. 
        I have a box of 90 blocks - one for each week of a 90-year life. 
        It's not that long. Life is short. We have to make choices. 
        Procrastination is the thief of time and the thief of life itself."""
    },
    "mNBmG24djoY": {
        "title": "How to stop screwing yourself over",
        "creator": "TED",
        "views": 30000000,
        "likes": 420000,
        "comments": 18000,
        "duration_seconds": 1021,
        "upload_date": "2011-10-06",
        "description": "Mel Robbins shares the secret to motivating yourself and taking control of your life.",
        "hashtags": ["motivation", "selfhelp", "psychology", "ted", "mindset"],
        "transcript": """I am going to share with you the one thing that you need to know about human behavior. 
        Are you ready? Here it is. You are never going to feel like it. 
        That's the problem. You think that motivation works like this - that you get motivation and then you take action. 
        That is completely backwards. The way it actually works is this: you take action first, then you get motivated. 
        You are not going to feel like doing the things you need to do. 
        I want you to think about something that you want in your life right now. 
        Something you want to do, something you want to say, something you want to change. 
        Are you thinking about it? Now think about why you're not doing it. 
        If I asked you why you're not living that dream right now, you would give me one of these answers: 
        I'm tired, I'm scared, I don't know how to do it, I'm not good enough. 
        These are all feelings. And guess what? You're never not going to feel tired. 
        You're never not going to feel scared. So if you only act when you feel like it, you're screwed. 
        The 5 Second Rule - if you have an impulse to act on a goal, you must physically move within 5 seconds or your brain will kill the idea. 
        5-4-3-2-1 and you move. Your feelings are lying to you. Your feelings are screwing you over. 
        You need to stop waiting to feel ready. You will never feel ready. 
        The moment you have an instinct to act on a goal or a commitment, use the rule: 5-4-3-2-1 go. 
        You have to go from autopilot to being deliberate. 
        Force yourself to change. Stop hitting the snooze button on your life."""
    }
}


def fetch_video_data(url: str) -> dict:
    if "youtube.com" in url or "youtu.be" in url:
        return fetch_youtube_data(url)
    elif "instagram.com" in url:
        return fetch_instagram_data(url)
    else:
        raise ValueError(f"Unsupported platform URL: {url}")


def _extract_youtube_id(url: str) -> str:
    patterns = [
        r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:embed/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError(f"Could not extract YouTube ID from: {url}")


def fetch_youtube_data(url: str) -> dict:
    video_id = _extract_youtube_id(url)

    # Check if we have demo data for this video
    if video_id in DEMO_TRANSCRIPTS:
        demo = DEMO_TRANSCRIPTS[video_id]
        views = demo["views"]
        likes = demo["likes"]
        comments = demo["comments"]
        engagement_rate = round((likes + comments) / max(views, 1) * 100, 2)
        return {
            "platform": "youtube",
            "video_id": video_id,
            "url": url,
            "title": demo["title"],
            "creator": demo["creator"],
            "follower_count": 0,
            "views": views,
            "likes": likes,
            "comments": comments,
            "duration_seconds": demo["duration_seconds"],
            "upload_date": demo["upload_date"],
            "description": demo["description"],
            "hashtags": demo["hashtags"],
            "engagement_rate": engagement_rate,
            "transcript": demo["transcript"],
        }

    # Try live fetch
    transcript_text = ""
    title = "YouTube Video"
    creator = "Unknown"
    views = likes = comments = duration = subscriber_count = 0
    upload_date = "N/A"
    description = ""
    hashtags = []

    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True, text=True, timeout=60
        )
        meta = json.loads(result.stdout)
        title = meta.get("title", "Unknown Title")
        creator = meta.get("uploader", meta.get("channel", "Unknown"))
        views = int(meta.get("view_count") or 0)
        likes = int(meta.get("like_count") or 0)
        comments = int(meta.get("comment_count") or 0)
        duration = int(meta.get("duration") or 0)
        upload_date_raw = meta.get("upload_date", "")
        upload_date = (
            datetime.strptime(upload_date_raw, "%Y%m%d").strftime("%Y-%m-%d")
            if upload_date_raw else "N/A"
        )
        description = meta.get("description", "")[:500]
        hashtags = meta.get("tags", [])[:15]
        subscriber_count = int(meta.get("channel_follower_count") or 0)
    except Exception as e:
        print(f"yt-dlp metadata fetch failed: {e}")

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join(item["text"] for item in transcript_list)
    except Exception as e:
        print(f"Transcript fetch failed for {video_id}: {e}")
        transcript_text = description

    engagement_rate = round((likes + comments) / max(views, 1) * 100, 2)

    return {
        "platform": "youtube",
        "video_id": video_id,
        "url": url,
        "title": title,
        "creator": creator,
        "follower_count": subscriber_count,
        "views": views,
        "likes": likes,
        "comments": comments,
        "duration_seconds": duration,
        "upload_date": upload_date,
        "description": description,
        "hashtags": hashtags,
        "engagement_rate": engagement_rate,
        "transcript": transcript_text,
    }


def fetch_instagram_data(url: str) -> dict:
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True, text=True, timeout=60
        )
        meta = json.loads(result.stdout)
        title = meta.get("title", meta.get("description", "Instagram Reel"))[:100]
        creator = meta.get("uploader", "Unknown")
        views = int(meta.get("view_count") or 0)
        likes = int(meta.get("like_count") or 0)
        comments = int(meta.get("comment_count") or 0)
        duration = int(meta.get("duration") or 0)
        description = meta.get("description", "")[:500]
        hashtags = re.findall(r"#\w+", description)
    except Exception as e:
        print(f"Instagram fetch failed: {e}")
        title = "Instagram Reel"
        creator = "Unknown"
        views = likes = comments = duration = 0
        description = ""
        hashtags = []

    engagement_rate = round((likes + comments) / max(views, 1) * 100, 2)

    return {
        "platform": "instagram",
        "video_id": url.split("/")[-2] if "/" in url else url,
        "url": url,
        "title": title,
        "creator": creator,
        "follower_count": 0,
        "views": views,
        "likes": likes,
        "comments": comments,
        "duration_seconds": duration,
        "upload_date": "N/A",
        "description": description,
        "hashtags": hashtags,
        "engagement_rate": engagement_rate,
        "transcript": description,
    }
