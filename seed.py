#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  WRITERSWORLD — Demo Data Seeder
#  Run once: python3 seed.py
# ─────────────────────────────────────────────

import sys, os
sys.path.insert(0, os.path.expanduser("~/writersworld"))
os.chdir(os.path.expanduser("~/writersworld"))

from app import app, db
from database import User, Story, Comment, Notification
from werkzeug.security import generate_password_hash
from datetime import datetime

USERS = [
    ("Amara",    "amara@test.com"),
    ("Chidi",    "chidi@test.com"),
    ("Fatima",   "fatima@test.com"),
    ("Emeka",    "emeka@test.com"),
    ("Ngozi",    "ngozi@test.com"),
    ("Kwame",    "kwame@test.com"),
    ("Aisha",    "aisha@test.com"),
    ("Tobias",   "tobias@test.com"),
    ("Yemi",     "yemi@test.com"),
    ("Sade",     "sade@test.com"),
    ("Malik",    "malik@test.com"),
    ("Zara",     "zara@test.com"),
    ("Kofi",     "kofi@test.com"),
    ("Chisom",   "chisom@test.com"),
    ("Adaeze",   "adaeze@test.com"),
    ("Tunde",    "tunde@test.com"),
    ("Halima",   "halima@test.com"),
    ("Seun",     "seun@test.com"),
    ("Nneka",    "nneka@test.com"),
    ("Jide",     "jide@test.com"),
]

STORIES = [
    ("The Last Candle",        "Romance",    "She had kept the candle burning for seven years, waiting for a man who promised to return before it went out. On the night it flickered its last, she heard a knock.\n\nShe opened the door. He stood there, older, quieter, a scar running down his jaw she did not recognise. The candle died between them.\n\n'I thought you were gone,' she whispered.\n\n'I thought you would have moved on,' he said.\n\nNeither of them moved. Outside, the rain began."),
    ("Iron Teeth",             "Action",     "The general had no name. Only a title — Iron Teeth — earned the night he bit through a chain that bound his wrists and strangled the man who put it there.\n\nNow he stood before a city of a million souls and one impossible order: burn it, or lose his own family.\n\nHe looked at his sword. Then at the city. Then at the letter from his commander.\n\nHe chose a third option no one had considered."),
    ("The Memory Merchant",    "Fantasy",    "In the floating markets of Yara, you could buy anything — spices, silk, stolen hours, forgotten faces. But only one merchant sold memories.\n\nShe kept them in glass vials, sorted by colour. Red for passion. Blue for grief. Gold for the moments people wished they could relive.\n\nA boy came in with empty eyes and asked for the most expensive thing she had.\n\n'That would be hope,' she said. 'And it is not for sale.'"),
    ("Signal Lost",            "Sci-Fi",     "The distress signal had been broadcasting from the dark side of Europa for forty-three years before anyone with the right equipment finally heard it.\n\nCommander Osei was not supposed to answer it. Protocol was clear. Uncharted signals meant quarantine, review, committee approval.\n\nShe answered it anyway.\n\nThe voice on the other end was her own, speaking in a language she had not yet learned."),
    ("The Quiet House",        "Horror",     "The estate agent said the house had been empty for twelve years. She said it like it was a selling point.\n\nOn the first night, Marcus counted seventeen doors. He had only seen sixteen when he moved in.\n\nOn the second night, he counted fifteen.\n\nOn the third night, he did not count. He simply sat in the centre of the floor and waited to see which door would open on its own."),
    ("Two Names",              "Drama",      "She had grown up with two names. The one her mother gave her, soft and full of meaning in a language her school friends could not pronounce. And the one she gave herself at thirteen, plain and easy and safe.\n\nAt thirty-two, she met a man who asked which one she preferred.\n\nIt was the first time anyone had asked.\n\nShe cried for four minutes in a restaurant bathroom before she could answer."),
    ("The Cartographer",       "Adventure",  "Every map Ezra drew was wrong. Not by accident — by design. He left errors in the edges, false rivers in the south, mountain ranges that did not exist.\n\nBecause some places were never meant to be found.\n\nWhen the soldiers arrived at his workshop demanding the real map, he smiled and handed them the most accurate one he had ever made.\n\nIt led directly into the sea."),
    ("Laughing at Funerals",   "Comedy",     "My grandmother's final wish was that nobody cry at her funeral. She was very specific about this. She left written instructions, a playlist, and a hired comedian.\n\nThe comedian got lost on the way. The playlist turned out to be exclusively Afrobeats. And my uncle, who had not cried since 1987, sobbed so hard he fell off his chair.\n\nGrandma would have loved every second of it."),
    ("The Algorithm",          "Thriller",   "The system flagged her as a threat at 6:04 AM on a Tuesday. By 6:09, her bank account was frozen. By 6:15, she was being escorted from her office building.\n\nThe problem was simple: she had found the flaw in the algorithm. And the algorithm, designed to protect itself, had decided she was the flaw.\n\nShe had forty-eight hours before her identity was officially erased. She had forty-seven hours of evidence."),
    ("Where the River Bends",  "Mystery",    "Three people had drowned in the same bend of the Akura River in three consecutive years. Different ages. Different circumstances. No connection.\n\nExcept one: all three had visited the old woman who lived in the yellow house on the hill the week before they died.\n\nDetective Abara knocked on the yellow door with one question ready.\n\nThe old woman opened it before he could knock twice. 'I wondered when you would come,' she said."),
    ("The Last Exam",          "Drama",      "He had failed the entrance exam four times. Each time, his mother said nothing — just reheated the soup and set it in front of him without a word.\n\nThe fifth time, he did not go home immediately. He sat outside the examination hall for three hours, watching strangers celebrate.\n\nWhen he finally got home, the soup was warm. She had been reheating it all day.\n\nHe passed the next year. She never mentioned the five attempts. Not once."),
    ("Daughters of Thunder",   "Fantasy",    "They were born during the storm that swallowed the old king. The midwife said it was a sign. The priests said it was a curse. The twins said nothing — they were newborns.\n\nBut seventeen years later, when lightning answered their anger and wind bent at their grief, the priests changed their story.\n\nThey always do."),
    ("The Penultimate Day",    "Sci-Fi",     "Scientists confirmed the asteroid would hit in thirty-one days. Governments collapsed in thirty. What surprised everyone was what people did with the remaining day.\n\nThey did not panic. They cooked. They called. They sat on rooftops and watched the sky turn colours no atmosphere should produce.\n\nAnd on the last morning, they discovered the scientists had miscalculated by exactly one century."),
    ("Night Market",           "Mystery",    "The market only appeared between 2 and 4 AM, in the space between the shuttered pharmacy and the wall that had no business being there.\n\nYou could buy things there that did not exist in daylight. Regrets bottled in amber. Silences that lasted exactly as long as you needed. Truth, sold by the gram.\n\nThe inspector had been investigating it for six months. Last Tuesday, she bought something she should not have.\n\nNow she understood why no one ever reported it to the authorities."),
    ("One Hundred Letters",    "Romance",    "He wrote to her every week for two years while she was abroad. She received none of the letters.\n\nThe postal service had been routing them to the wrong address — a bakery in the north of the city.\n\nThe baker read every one. When the woman finally returned home, the baker was the first person at the airport.\n\n'I know this is strange,' she said, holding a bundle of envelopes. 'But I think these belong to you. And I think I am in love with the man who wrote them.'"),
    ("The Inheritance",        "Drama",      "Their father left them one house and no instructions.\n\nThe eldest wanted to sell. The second wanted to keep it. The third had not been back in eleven years and said nothing at all.\n\nThey sat in the kitchen of the house for seven hours. By midnight, they had said things to each other they had been holding for decades.\n\nBy morning, they had made a decision. This story is about the seven hours, not the decision."),
    ("Borrowed Light",         "Poetry",     "The moon does not generate its own light.\nIt borrows from the sun and calls it beautiful.\n\nI have been doing the same thing for years —\nborrowing joy from others,\nreflecting it back as my own warmth,\nand wondering why I feel cold\nwhen they look away.\n\nTonight I am practising making my own light.\nIt is small. Unsteady. Barely visible.\n\nBut it is mine."),
    ("The Surgeon's Hands",    "Thriller",   "She had performed over three thousand operations without a single fatality. Her hands were famous — steady, precise, almost inhuman in their calm.\n\nBut that was before she recognised the man on the table.\n\nHe was the one who had taken everything from her six years ago. He did not recognise her behind the mask.\n\nThe team waited. The monitor beeped. She picked up the scalpel.\n\nAnd she performed the four thousand and first perfect operation of her career."),
    ("The Student and the Sea", "Adventure", "She was seventeen when she swam out too far and the current took her. She was found three days later on an island that did not appear on any map.\n\nThe island had a library. The library had one book. The book was about her.\n\nIt described her life in detail up to the moment she swam out too far, and then the rest of the pages were blank.\n\nShe picked up the pen that was sitting on the desk and began to write."),
    ("What We Bury",           "Horror",     "The town had a rule: you do not speak about what you bury in the east field. Not the objects. Not the reasons. Not the dates.\n\nNadia had grown up with the rule and never questioned it.\n\nUntil she found her own name on one of the markers.\n\nWith a date that was three days from now."),
]

GENRES = ["General","Romance","Action","Fantasy","Sci-Fi",
          "Horror","Mystery","Comedy","Drama","Thriller",
          "Adventure","Historical","Poetry","Other"]

with app.app_context():
    # Check if already seeded
    existing = User.query.filter_by(is_admin=False).count()
    if existing >= 10:
        print(f"Already seeded ({existing} users). Skipping.")
        sys.exit(0)

    print("Seeding demo data...")

    # Create users
    created_users = []
    for username, email in USERS:
        if not User.query.filter_by(email=email).first():
            u = User(
                username=username,
                email=email,
                password=generate_password_hash("123456"),
                bio=f"Writer and storyteller. Passionate about great stories.",
                is_admin=False,
                joined=datetime.utcnow()
            )
            db.session.add(u)
            db.session.flush()
            created_users.append(u)
            print(f"  Created user: {username}")

    db.session.commit()

    # Create stories — one per user for first 20 users
    all_users = User.query.filter_by(is_admin=False).all()
    for i, (title, genre, content) in enumerate(STORIES):
        if i >= len(all_users):
            break
        author = all_users[i]
        if not Story.query.filter_by(title=title).first():
            s = Story(
                title=title,
                content=content,
                genre=genre,
                is_published=True,
                views=0,
                user_id=author.id,
                created_at=datetime.utcnow()
            )
            db.session.add(s)
            print(f"  Created story: {title} by {author.username}")

    db.session.commit()

    # Add some follows
    users = User.query.filter_by(is_admin=False).all()
    for i, u in enumerate(users[:10]):
        next_u = users[(i+1) % len(users)]
        if not u.is_following(next_u):
            u.follow(next_u)

    db.session.commit()

    # Add some comments
    stories = Story.query.filter_by(is_published=True).all()
    comment_texts = [
        "This is beautifully written. I could not stop reading.",
        "The ending caught me completely off guard. Brilliant.",
        "I felt every word of this. Thank you for sharing.",
        "This deserves so many more readers.",
        "The imagery here is stunning. Really vivid writing.",
    ]
    for i, story in enumerate(stories[:10]):
        commenter = users[(i+2) % len(users)]
        c = Comment(
            content=comment_texts[i % len(comment_texts)],
            user_id=commenter.id,
            story_id=story.id,
            created_at=datetime.utcnow()
        )
        db.session.add(c)

    db.session.commit()
    print("\nDemo data seeded successfully!")
    print(f"  Users: {len(USERS)}")
    print(f"  Stories: {len(STORIES)}")
    print("  All user passwords: 123456")
