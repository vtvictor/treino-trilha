alter table public.exercises
add column if not exists series_total integer not null default 3;

alter table public.exercises
add column if not exists series_done integer not null default 0;

update public.exercises
set
    series_total = case
        when series_total is null or series_total < 1 then 1
        else series_total
    end,
    series_done = case
        when done = true then
            case
                when series_total is null or series_total < 1 then 1
                else series_total
            end
        else 0
    end;

alter table public.workout_history
add column if not exists series_total integer not null default 0;

alter table public.workout_history
add column if not exists series_done integer not null default 0;
