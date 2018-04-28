drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  title text not null,
  query text not null,
  result text
);
