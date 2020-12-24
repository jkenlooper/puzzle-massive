update User set points = :minimum where points < :minimum or points is null;
