insert into Attribution (
    title, -- title of work
    author_link, -- link to author's profile page
    author_name,
    source, -- link to page showing the image
    license
) values (
    :title,
    :author_link,
    :author_name,
    :source,
    (select id from License where name = :license_name)
);
