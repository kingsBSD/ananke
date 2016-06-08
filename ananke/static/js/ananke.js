var mainModule = angular.module('ananke-main',['angularSpinners']);
            
mainModule.controller('nodeController',function($scope,$http,spinnerService) {
    
    $scope.status = "dormant";
    $scope.chunk3 = {};
    $scope.chunk4 = {};
    $scope.error = {};
    $scope.slave_ip = false;
    $scope.slave_owner = {"active":false};
    $scope.master_owner = false;
    $scope.pysparknotebook = false;
    
    var msg = {'master_active':0, 'slave_active':1, 'notebook_active':2, 'stopped_pysparknotebook':3,
        'stopped_sparkmaster':4, 'stopped_sparkslave':5, 'node_active':6, 'stopped_singlenode':7};
    
    $http.get('api/status',{params: {}}).success(function(data, status, headers, config) {
        if (data.network) {
            $scope.ipchunks = [{i:data.ip[0]}, {i:data.ip[1]}];
            $scope.master_url = data.ip.join('.')+":8080";
            $scope.slave_ip = data.slave_ip;
            $scope.master_owner = data.master_owner;
            $scope.pysparknotebook = data.pysparknotebook;
        }
        $scope.status = data.status;
    }).error(function(data, status, headers, config) {
        $scope.ipchunks = [{i:0}, {i:0}];
    });
    
    var auto_conn = new WebSocket("ws://127.0.0.1:5001");
    auto_conn.onopen = function() {
        auto_conn.send('local_socket');
    };
    
    auto_conn.onmessage = function(e) {
        var msChunks = e.data.split(" ")
        switch (parseInt(msg[msChunks[0]])) {
            case msg.master_active:
                $scope.status = 'active'; $scope.master_owner = true; $scope.master_ip = msChunks[1]; spinnerService.hide('wait'); $scope.$apply(); break;
            case msg.slave_active:
                $scope.status = 'active'; $scope.slave_ip = msChunks[1]; $scope.slave_owner.active = true; spinnerService.hide('wait'); $scope.$apply(); break;
            case msg.notebook_active:
                $scope.status = 'active'; $scope.pysparknotebook = true; spinnerService.hide('wait'); $scope.$apply(); break;
            case msg.stopped_pysparknotebook:
                $scope.status = 'active'; $scope.pysparknotebook = false; spinnerService.hide('wait'); $scope.$apply(); break;
            case msg.stopped_sparkmaster:
                $scope.status = 'dormant'; $scope.master_owner = false; spinnerService.hide('wait'); $scope.$apply(); break;
            case msg.stopped_sparkslave:
                $scope.status = 'dormant'; $scope.slave_owner.active = false; $scope.slave_ip = false; spinnerService.hide('wait'); $scope.$apply(); break;
            case msg.node_active: $scope.status = "single"; spinnerService.hide('wait'); $scope.$apply(); break;
            case msg.stopped_singlenode: $scope.status = 'dormant'; spinnerService.hide('wait'); $scope.$apply(); break;          
        }    
    }    
                            
    $scope.start_cluster = function() {
        $scope.status = 'waiting';
        spinnerService.show('wait');
        $http.get('api/startcluster',{params: {}}).success(function(data, status, headers, config) {
            if (!data.okay) {
                $scope.error.msg = data.error;
                $scope.status = 'dormant';
                spinnerService.hide('wait');    
            }    
        }).error(function(data, status, headers, config) {});
    };
    
    $scope.join_cluster = function() {
        $scope.status = 'waiting';
        spinnerService.show('wait');
        var master_ip = ([$scope.ipchunks[0].i, $scope.ipchunks[1].i, $scope.chunk3.i, $scope.chunk4.i]).join('.');
        $scope.master_ip = master_ip
        $http.get('api/joincluster',{params: {'ip':master_ip}}).success(function(data, status, headers, config) {
            $scope.master_url = master_ip+":8080";
            if (!data.okay) {
                $scope.error.msg = data.error;
                $scope.status = 'dormant';
                spinnerService.hide('wait');    
            } 
        }).error(function(data, status, headers, config) {});
    };
    
    $scope.notebook_cluster = function() {
        $scope.status = 'waiting';
        spinnerService.show('wait');
        $http.get('api/startclusternotebook',{params: {'ip':$scope.master_ip}}).success(function(data, status, headers, config) {
            if (!data.okay) {
                $scope.error.msg = data.error;
                spinnerService.hide('wait');     
            }
        }).error(function(data, status, headers, config) {});
    };
    
    $scope.cluster_notebook_stop = function() {
        simple_service('api/stopclusternotebook');
    };
 
    $scope.stop_cluster = function() {
        simple_service('api/stopcluster');
    };
    
    $scope.leave_cluster = function() {
        simple_service('/api/leavecluster');
    };
    
    $scope.start_single_node = function() {
        simple_service('/api/startsinglenotebook');
    };
    
    $scope.single_notebook_stop = function() {
        simple_service('/api/stopsinglenotebook');
    };
    
    simple_service = function(endpoint) {
        $scope.status = 'waiting';
        spinnerService.show('wait');
        $http.get(endpoint,{params: {}}).success(function(data, status, headers, config) {
            if (!data.okay) {
                $scope.error.msg = data.error;
                spinnerService.hide('wait');     
            }
        }).error(function(data, status, headers, config) {});  
    };    
 
});

mainModule.controller('docController',function($scope,$http) {
    
    $http.get('api/getdocs',{params: {}}).success(function(data, status, headers, config) {
        $scope.allthedocs = data.allthedocs;
    }).error(function(data, status, headers, config) {
    });    

    
});    