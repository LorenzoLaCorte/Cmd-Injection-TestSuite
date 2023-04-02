<?php

$host = $_GET['host'];

shell_exec(escapeshellcmd("ping -c 3 $host"));
