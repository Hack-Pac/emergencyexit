import SwiftUI
import MapKit

struct ContentView: View {
    var body: some View {
        NavigationView {
            TabView {
                MapView()
                    .tabItem {
                        Image(systemName: "map.fill")
                        Text("Map")
                    }
                
                AlertsView()
                    .tabItem {
                        Image(systemName: "exclamationmark.triangle.fill")
                        Text("Alerts")
                    }
                
                StatsView()
                    .tabItem {
                        Image(systemName: "chart.bar.fill")
                        Text("Stats")
                    }
                
                ContactsView()
                    .tabItem {
                        Image(systemName: "phone.fill")
                        Text("Contacts")
                    }
            }
            .accentColor(.red)
        }
    }
}

struct MapView: View {
    @State private var startLocation = ""
    @State private var endLocation = ""
    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 37.7749, longitude: -122.4194),
        span: MKCoordinateSpan(latitudeDelta: 0.1, longitudeDelta: 0.1)
    )
    
    var body: some View {
        VStack(spacing: 0) {
            Map(coordinateRegion: $region)
                .frame(height: 300)
                .overlay(
                    VStack {
                        Spacer()
                        Text("Emergency Exit Route")
                            .font(.headline)
                            .padding(8)
                            .background(Color.black.opacity(0.7))
                            .foregroundColor(.white)
                            .cornerRadius(8)
                    }.padding(.bottom)
                )
            
            VStack(spacing: 16) {
                LocationInputField(icon: "mappin.circle.fill", placeholder: "Start Location", text: $startLocation)
                LocationInputField(icon: "mappin.and.ellipse", placeholder: "End Location", text: $endLocation)
                
                Button(action: {
                    // Action to find safe route
                }) {
                    Text("Find Safe Route")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.red)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }
            }
            .padding()
            .background(Color.white)
            .cornerRadius(20)
            .shadow(radius: 5)
            .padding()
            
            Spacer()
        }
        .navigationTitle("Emergency Exit")
        .background(Color.gray.opacity(0.1))
    }
}

struct LocationInputField: View {
    let icon: String
    let placeholder: String
    @Binding var text: String
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(.red)
            TextField(placeholder, text: $text)
        }
        .padding()
        .background(Color.white)
        .cornerRadius(10)
        .shadow(color: .gray.opacity(0.2), radius: 5, x: 0, y: 2)
    }
}

struct AlertsView: View {
    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                AlertCard(type: .error, title: "Wildfire Alert", message: "Mandatory evacuation for Sunset District. Leave immediately.")
                AlertCard(type: .warning, title: "High Wind Advisory", message: "Gusty winds expected in the hill areas.")
                AlertCard(type: .info, title: "Air Quality Warning", message: "Unhealthy air quality levels due to smoke.")
            }
            .padding()
        }
        .navigationTitle("Emergency Alerts")
        .background(Color.gray.opacity(0.1))
    }
}

struct AlertCard: View {
    enum AlertType {
        case error, warning, info
    }
    
    let type: AlertType
    let title: String
    let message: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: iconName)
                    .foregroundColor(.white)
                    .padding(8)
                    .background(iconColor)
                    .clipShape(Circle())
                
                Text(title)
                    .font(.headline)
            }
            
            Text(message)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            Button(action: {
                // Action for more details
            }) {
                Text("More Details")
                    .font(.caption)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(iconColor.opacity(0.2))
                    .foregroundColor(iconColor)
                    .cornerRadius(15)
            }
        }
        .padding()
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: .gray.opacity(0.2), radius: 5, x: 0, y: 2)
    }
    
    private var iconName: String {
        switch type {
        case .error: return "exclamationmark.triangle.fill"
        case .warning: return "exclamationmark.circle.fill"
        case .info: return "info.circle.fill"
        }
    }
    
    private var iconColor: Color {
        switch type {
        case .error: return .red
        case .warning: return .orange
        case .info: return .blue
        }
    }
}

struct StatsView: View {
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                StatCard(title: "Air Quality Index", value: "150", detail: "Unhealthy", color: .orange)
                StatCard(title: "Fire Spread Rate", value: "15 mph", detail: "High", color: .red)
                StatCard(title: "Wind Speed", value: "25 mph", detail: "Strong", color: .blue)
                
                EmergencyLevelGauge()
            }
            .padding()
        }
        .navigationTitle("Emergency Statistics")
        .background(Color.gray.opacity(0.1))
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let detail: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)
                .foregroundColor(.secondary)
            
            HStack(alignment: .lastTextBaseline) {
                Text(value)
                    .font(.system(size: 36, weight: .bold))
                    .foregroundColor(color)
                
                Text(detail)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            ProgressView(value: Double.random(in: 0...1))
                .accentColor(color)
        }
        .padding()
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: .gray.opacity(0.2), radius: 5, x: 0, y: 2)
    }
}

struct EmergencyLevelGauge: View {
    @State private var emergencyLevel: Double = 0.7
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Current Emergency Level")
                .font(.headline)
            
            Gauge(value: emergencyLevel, in: 0...1) {
                Text("Level")
            } currentValueLabel: {
                Text("\(Int(emergencyLevel * 100))%")
            } minimumValueLabel: {
                Text("Low")
            } maximumValueLabel: {
                Text("High")
            }
            .gaugeStyle(.accessoryCircular)
            .tint(Gradient(colors: [.green, .yellow, .orange, .red]))
            .scaleEffect(1.5)
        }
        .padding()
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: .gray.opacity(0.2), radius: 5, x: 0, y: 2)
    }
}

struct ContactsView: View {
    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                ContactCard(name: "Fire Department", number: "911", icon: "flame.fill", color: .red)
                ContactCard(name: "Police", number: "911", icon: "shield.fill", color: .blue)
                ContactCard(name: "Ambulance", number: "911", icon: "cross.fill", color: .green)
                ContactCard(name: "Evacuation Helpline", number: "555-0123", icon: "megaphone.fill", color: .orange)
            }
            .padding()
        }
        .navigationTitle("Emergency Contacts")
        .background(Color.gray.opacity(0.1))
    }
}

struct ContactCard: View {
    let name: String
    let number: String
    let icon: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 24))
                .foregroundColor(.white)
                .frame(width: 50, height: 50)
                .background(color)
                .clipShape(Circle())
            
            VStack(alignment: .leading, spacing: 4) {
                Text(name)
                    .font(.headline)
                Text(number)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Button(action: {
                // Action to call the number
                guard let url = URL(string: "tel://\(number)") else { return }
                UIApplication.shared.open(url)
            }) {
                Image(systemName: "phone.fill")
                    .foregroundColor(.white)
                    .padding(10)
                    .background(color)
                    .clipShape(Circle())
            }
        }
        .padding()
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: .gray.opacity(0.2), radius: 5, x: 0, y: 2)
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}