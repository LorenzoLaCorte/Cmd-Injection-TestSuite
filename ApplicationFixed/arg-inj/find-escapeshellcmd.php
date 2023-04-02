<?php

$input = $_GET['input'];

system(escapeshellarg("find . -name $input"));
