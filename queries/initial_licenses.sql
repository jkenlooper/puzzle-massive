insert into License (source, name, title) values
(
    'https://unsplash.com/?utm_source=' || :application_name || '&utm_medium=referral',
    'unsplash',
    'Unsplash'
);
