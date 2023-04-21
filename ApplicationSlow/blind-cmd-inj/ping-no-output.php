<?php

$host = $_GET['host'];

shell_exec("ping -c 10 $host");
