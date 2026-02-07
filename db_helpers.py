import os
import psycopg2


def get_db_connection():
    connection = psycopg2.connect(
        host='localhost',
        database=os.getenv('POSTGRES_DATABASE'),
        user=os.getenv('POSTGRES_USERNAME'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    return connection


def consolidate_comments_in_hoots(hoots_with_comments):
    print(hoots_with_comments)
    consolidated_hoots = []
    for hoot in hoots_with_comments:
        # Check if this hoot has already been added to consolidated_hoots
        hoot_exists = False
        for consolidated_hoot in consolidated_hoots:
            if hoot["id"] == consolidated_hoot["id"]:
                hoot_exists = True
                consolidated_hoot["comments"].append(
                    {"comment_text": hoot["comment_text"],
                     "comment_id": hoot["comment_id"],
                     "comment_author_username": hoot["comment_author_username"]
                     })
                break

        # If the hoot doesn't exist in consolidated_hoots, add it
        if not hoot_exists:
            hoot["comments"] = []
            if hoot["comment_id"] is not None:
                hoot["comments"].append(
                    {"comment_text": hoot["comment_text"],
                     "comment_id": hoot["comment_id"],
                     "comment_author_username": hoot["comment_author_username"]
                     }
                )
            del hoot["comment_id"]
            del hoot["comment_text"]
            del hoot["comment_author_username"]
            consolidated_hoots.append(hoot)

    return consolidated_hoots
