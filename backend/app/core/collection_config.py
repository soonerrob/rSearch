"""Configuration for post and comment collection."""

POST_COLLECTION_CONFIG = {
    'distribution': {
        'hot': {
            'weight': 0.3,
            'min_score': 10
        },
        'top': {
            'weight': 0.3,
            'time_filters': ['month', 'week'],
            'min_score': 15
        },
        'rising': {
            'weight': 0.2,
            'min_score': 5
        },
        'controversial': {
            'weight': 0.2,
            'min_score': 5
        }
    },
    'quality_filters': {
        'min_upvote_ratio': 0.65,
        'min_comments': 5,
        'exclude_removed': True
    }
}

COMMENT_COLLECTION_CONFIG = {
    'depth_settings': {
        'top_level': {
            'limit': 25,
            'min_score': 5
        },
        'replies': {
            'max_depth': 5,
            'min_score_by_depth': {
                1: 4,  # First-level replies
                2: 3,  # Second-level replies
                3: 2,  # Third-level replies
                'default': 1
            }
        }
    },
    'sort_methods': {
        'best': {'limit': 15},
        'top': {'limit': 15},
        'controversial': {'limit': 10},
        'qa': {'limit': 10}
    }
}

COMMENT_QUALITY_FILTERS = {
    'min_length': 20,
    'exclude_deleted': True,
    'exclude_removed': True,
    'require_author': True,
    'engagement_multipliers': {
        'is_submitter': 1.5,
        'distinguished': 1.3,
        'awarded': 1.2
    }
} 